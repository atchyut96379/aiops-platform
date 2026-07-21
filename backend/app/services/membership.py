from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.core.security import hash_opaque_token, hash_password, verify_password
from app.models.enums import InviteStatus, RoleName
from app.models.organization import Organization
from app.models.organization_invite import OrganizationInvite
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.audit import AuditLogRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.organization_invite import OrganizationInviteRepository
from app.repositories.role import RoleRepository, UserRoleRepository
from app.repositories.user import UserRepository
from app.schemas.auth import AcceptInviteRequest
from app.schemas.common import TokenPair
from app.schemas.membership import (
    MemberRolesUpdate,
    OrganizationInviteCreate,
    OrganizationMemberResponse,
)
from app.schemas.organization import OrganizationCreate
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.services.email import EmailService
from app.utils.slug import slugify
from app.utils.tokens import generate_url_safe_token


class MembershipService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.orgs = OrganizationRepository(db)
        self.roles = RoleRepository(db)
        self.memberships = UserRoleRepository(db)
        self.invites = OrganizationInviteRepository(db)
        self.audit = AuditLogRepository(db)
        self.email = EmailService()

    def list_members(
        self, *, organization_id: int, requester: User
    ) -> list[OrganizationMemberResponse]:
        self._require_org_admin(requester, organization_id)
        memberships = self.memberships.list_for_organization(organization_id)
        members_map: dict[int, list[str]] = {}
        users_map: dict[int, User] = {}

        for membership in memberships:
            if membership.user is None or membership.role is None:
                continue
            users_map[membership.user_id] = membership.user
            members_map.setdefault(membership.user_id, []).append(membership.role.name)

        return [
            OrganizationMemberResponse(
                user=UserResponse.model_validate(users_map[user_id]),
                roles=sorted(set(roles)),
            )
            for user_id, roles in members_map.items()
        ]

    def update_member_roles(
        self,
        *,
        organization_id: int,
        user_id: int,
        payload: MemberRolesUpdate,
        requester: User,
    ) -> OrganizationMemberResponse:
        self._require_org_admin(requester, organization_id)
        target = self.users.get(user_id)
        if target is None:
            raise NotFoundError("User not found")

        existing = self.memberships.list_for_user_org(user_id, organization_id)
        if not existing and not target.is_superuser:
            raise NotFoundError("User is not a member of this organization")

        if user_id == requester.id and RoleName.ORGANIZATION_ADMIN.value not in {
            r.value for r in payload.roles
        }:
            admin_count = self._count_org_admins(organization_id)
            if admin_count <= 1:
                raise ValidationAppError(
                    "Cannot remove the last organization admin",
                    code="last_admin",
                )

        self.memberships.delete_for_user_org(user_id, organization_id)
        role_names: list[str] = []
        for role_enum in payload.roles:
            role = self.roles.get_by_name(role_enum.value)
            if role is None:
                raise ValidationAppError(f"Unknown role: {role_enum.value}")
            membership = UserRole(
                user_id=user_id,
                organization_id=organization_id,
                role_id=role.id,
            )
            self.memberships.add(membership)
            role_names.append(role.name)

        self.audit.record(
            action="member.roles_updated",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="user",
            resource_id=str(user_id),
            details={"roles": role_names},
        )
        self.db.commit()
        return OrganizationMemberResponse(
            user=UserResponse.model_validate(target),
            roles=sorted(set(role_names)),
        )

    def remove_member(
        self, *, organization_id: int, user_id: int, requester: User
    ) -> None:
        self._require_org_admin(requester, organization_id)
        if user_id == requester.id:
            raise ValidationAppError("Cannot remove yourself from the organization")

        memberships = self.memberships.list_for_user_org(user_id, organization_id)
        if not memberships:
            raise NotFoundError("User is not a member of this organization")

        admin_roles = [m for m in memberships if m.role and m.role.name == RoleName.ORGANIZATION_ADMIN.value]
        if admin_roles and self._count_org_admins(organization_id) <= 1:
            raise ValidationAppError(
                "Cannot remove the last organization admin",
                code="last_admin",
            )

        self.memberships.delete_for_user_org(user_id, organization_id)
        target = self.users.get(user_id)
        if target and target.default_organization_id == organization_id:
            remaining = self.memberships.list_for_user(user_id)
            target.default_organization_id = (
                remaining[0].organization_id if remaining else None
            )

        self.audit.record(
            action="member.removed",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="user",
            resource_id=str(user_id),
        )
        self.db.commit()

    def create_invite(
        self,
        *,
        organization_id: int,
        payload: OrganizationInviteCreate,
        requester: User,
    ) -> OrganizationInvite:
        self._require_org_admin(requester, organization_id)
        email = payload.email.lower()

        existing_user = self.users.get_by_email(email)
        if existing_user:
            memberships = self.memberships.list_for_user_org(existing_user.id, organization_id)
            if memberships:
                raise ConflictError("User is already a member of this organization")

        pending = self.invites.get_pending_for_email(organization_id, email)
        if pending:
            raise ConflictError("A pending invite already exists for this email")

        role = self.roles.get_by_name(payload.role.value)
        if role is None:
            raise ValidationAppError("Invalid role")

        raw_token = generate_url_safe_token()
        invite = OrganizationInvite(
            organization_id=organization_id,
            email=email,
            role_id=role.id,
            token_hash=hash_opaque_token(raw_token),
            invited_by_user_id=requester.id,
            status=InviteStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.invites.add(invite)
        org = self.orgs.get(organization_id)
        self.email.send_organization_invite(
            to=email,
            token=raw_token,
            organization_name=org.name if org else "your organization",
        )
        self.audit.record(
            action="invite.created",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="invite",
            resource_id=str(invite.id),
            details={"email": email, "role": role.name},
        )
        self.db.commit()
        self.db.refresh(invite)
        return invite

    def list_invites(
        self, *, organization_id: int, requester: User
    ) -> Sequence[OrganizationInvite]:
        self._require_org_admin(requester, organization_id)
        self.invites.mark_expired_pending()
        self.db.commit()
        return self.invites.list_for_organization(organization_id)

    def revoke_invite(
        self, *, organization_id: int, invite_id: int, requester: User
    ) -> OrganizationInvite:
        self._require_org_admin(requester, organization_id)
        invite = self.invites.get(invite_id)
        if invite is None or invite.organization_id != organization_id:
            raise NotFoundError("Invite not found")
        if invite.status != InviteStatus.PENDING.value:
            raise ValidationAppError("Only pending invites can be revoked")

        invite.status = InviteStatus.REVOKED.value
        self.audit.record(
            action="invite.revoked",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="invite",
            resource_id=str(invite_id),
        )
        self.db.commit()
        self.db.refresh(invite)
        return invite

    def accept_invite(
        self,
        payload: AcceptInviteRequest,
        *,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[User, Organization, TokenPair]:
        token_hash = hash_opaque_token(payload.token)
        invite = self.invites.get_by_token_hash(token_hash)
        if invite is None:
            raise ValidationAppError("Invalid or expired invite", code="invalid_invite")

        expires_at = invite.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if invite.status != InviteStatus.PENDING.value or expires_at < datetime.now(timezone.utc):
            raise ValidationAppError("Invalid or expired invite", code="invalid_invite")

        role = invite.role
        if role is None:
            raise ValidationAppError("Invalid invite role")

        user = self.users.get_by_email(invite.email)
        if user is None:
            if not payload.first_name or not payload.last_name or not payload.password:
                raise ValidationAppError(
                    "New users must provide first_name, last_name, and password",
                    code="registration_required",
                )
            user = User(
                first_name=payload.first_name.strip(),
                last_name=payload.last_name.strip(),
                email=invite.email,
                hashed_password=hash_password(payload.password),
                is_active=True,
                is_email_verified=True,
                default_organization_id=invite.organization_id,
            )
            self.users.add(user)
        else:
            if payload.password and not verify_password(payload.password, user.hashed_password):
                raise ValidationAppError("Invalid password for existing account")
            if user.default_organization_id is None:
                user.default_organization_id = invite.organization_id

        if not self.memberships.exists(user.id, invite.organization_id, role.id):
            self.memberships.add(
                UserRole(
                    user_id=user.id,
                    organization_id=invite.organization_id,
                    role_id=role.id,
                )
            )

        invite.status = InviteStatus.ACCEPTED.value
        invite.accepted_at = datetime.now(timezone.utc)

        tokens = AuthService(self.db)._issue_token_pair(
            user,
            organization_id=invite.organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        org = self.orgs.get(invite.organization_id)
        if org is None:
            raise NotFoundError("Organization not found")

        self.audit.record(
            action="invite.accepted",
            user_id=user.id,
            organization_id=invite.organization_id,
            resource_type="invite",
            resource_id=str(invite.id),
        )
        self.db.commit()
        self.db.refresh(user)
        return user, org, tokens

    def create_organization(
        self, user: User, payload: OrganizationCreate
    ) -> Organization:
        slug = slugify(payload.name)
        if self.orgs.get_by_slug(slug) or self.orgs.get_by_name(payload.name):
            raise ConflictError("Organization name is already taken")

        org = Organization(
            name=payload.name,
            slug=slug,
            logo_url=payload.logo_url,
            description=payload.description,
            subscription_plan=payload.subscription_plan.value,
        )
        self.orgs.add(org)

        admin_role = self.roles.get_by_name(RoleName.ORGANIZATION_ADMIN.value)
        if admin_role is None:
            raise ValidationAppError("System roles are not seeded")

        self.memberships.add(
            UserRole(user_id=user.id, organization_id=org.id, role_id=admin_role.id)
        )
        if user.default_organization_id is None:
            user.default_organization_id = org.id

        self.audit.record(
            action="organization.created",
            user_id=user.id,
            organization_id=org.id,
            resource_type="organization",
            resource_id=str(org.id),
        )
        self.db.commit()
        self.db.refresh(org)
        return org

    def list_user_organizations(self, user: User) -> Sequence[Organization]:
        if user.is_superuser:
            return self.orgs.list_all()
        return self.orgs.list_for_user(user.id)

    def switch_organization(
        self,
        user: User,
        organization_id: int,
        *,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenPair:
        if not user.is_superuser:
            memberships = self.memberships.list_for_user_org(user.id, organization_id)
            if not memberships:
                raise ForbiddenError("Not a member of this organization")

        org = self.orgs.get(organization_id)
        if org is None or not org.is_active:
            raise NotFoundError("Organization not found")

        user.default_organization_id = organization_id
        tokens = AuthService(self.db)._issue_token_pair(
            user,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.audit.record(
            action="organization.switched",
            user_id=user.id,
            organization_id=organization_id,
        )
        self.db.commit()
        return tokens

    def _require_org_admin(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        memberships = self.memberships.list_for_user_org(user.id, organization_id)
        role_names = {m.role.name for m in memberships if m.role}
        if RoleName.ORGANIZATION_ADMIN.value not in role_names:
            raise ForbiddenError("Organization admin role required")

    def _count_org_admins(self, organization_id: int) -> int:
        memberships = self.memberships.list_for_organization(organization_id)
        return sum(
            1
            for m in memberships
            if m.role and m.role.name == RoleName.ORGANIZATION_ADMIN.value
        )
