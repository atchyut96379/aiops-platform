from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.models.enums import RoleName, SubscriptionPlan
from app.models.organization import Organization
from app.models.user import EmailVerificationToken, PasswordResetToken, RefreshToken, User
from app.models.user_role import UserRole
from app.repositories.audit import AuditLogRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.role import RoleRepository, UserRoleRepository
from app.repositories.user import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    RefreshTokenRepository,
    UserRepository,
)
from app.schemas.auth import RegisterRequest
from app.schemas.common import TokenPair
from app.services.email import EmailService
from app.utils.slug import slugify
from app.utils.tokens import generate_url_safe_token


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.orgs = OrganizationRepository(db)
        self.roles = RoleRepository(db)
        self.memberships = UserRoleRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.reset_tokens = PasswordResetTokenRepository(db)
        self.verify_tokens = EmailVerificationTokenRepository(db)
        self.audit = AuditLogRepository(db)
        self.email = EmailService()

    def register(
        self,
        payload: RegisterRequest,
        *,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[User, Organization, TokenPair]:
        if self.users.get_by_email(payload.email):
            raise ConflictError("Email is already registered", code="email_exists")

        slug = slugify(payload.organization_name)
        if self.orgs.get_by_slug(slug) or self.orgs.get_by_name(payload.organization_name):
            raise ConflictError(
                "Organization name is already taken",
                code="organization_exists",
            )

        org = Organization(
            name=payload.organization_name,
            slug=slug,
            subscription_plan=SubscriptionPlan.FREE.value,
        )
        self.orgs.add(org)

        user = User(
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            email=payload.email.lower(),
            hashed_password=hash_password(payload.password),
            is_active=True,
            is_email_verified=False,
            default_organization_id=org.id,
        )
        self.users.add(user)

        # Ensure default_organization_id is set after org flush
        user.default_organization_id = org.id
        self.db.flush()

        admin_role = self.roles.get_by_name(RoleName.ORGANIZATION_ADMIN.value)
        if admin_role is None:
            raise ValidationAppError("System roles are not seeded", code="roles_not_seeded")

        membership = UserRole(
            user_id=user.id,
            organization_id=org.id,
            role_id=admin_role.id,
        )
        self.memberships.add(membership)

        self._issue_email_verification(user)
        tokens = self._issue_token_pair(
            user,
            organization_id=org.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.audit.record(
            action="user.register",
            user_id=user.id,
            organization_id=org.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        from app.services.alert_rule import AlertRuleService

        AlertRuleService(self.db).seed_default_rules(org.id)
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(org)
        return user, org, tokens

    def login(
        self,
        *,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenPair:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password", code="invalid_credentials")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled", code="account_disabled")

        self.users.update_last_login(user)
        tokens = self._issue_token_pair(
            user,
            organization_id=user.default_organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.audit.record(
            action="user.login",
            user_id=user.id,
            organization_id=user.default_organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        return tokens

    def refresh(
        self,
        refresh_token: str,
        *,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenPair:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise UnauthorizedError("Invalid refresh token", code="invalid_refresh") from exc

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid refresh token type", code="invalid_refresh")

        jti = payload.get("jti")
        subject = payload.get("sub")
        if not jti or not subject:
            raise UnauthorizedError("Invalid refresh token", code="invalid_refresh")

        stored = self.refresh_tokens.get_by_jti(jti)
        if stored is None or stored.revoked:
            raise UnauthorizedError("Refresh token revoked or unknown", code="invalid_refresh")

        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise UnauthorizedError("Refresh token expired", code="refresh_expired")

        if stored.token_hash != hash_opaque_token(refresh_token):
            raise UnauthorizedError("Refresh token mismatch", code="invalid_refresh")

        user = self.users.get(int(subject))
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive", code="invalid_refresh")

        # Rotate: revoke old, issue new
        self.refresh_tokens.revoke(stored)
        tokens = self._issue_token_pair(
            user,
            organization_id=user.default_organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.audit.record(
            action="user.token_refresh",
            user_id=user.id,
            organization_id=user.default_organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        return tokens

    def logout(
        self,
        refresh_token: str,
        *,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
        except ValueError:
            jti = None

        if jti:
            stored = self.refresh_tokens.get_by_jti(jti)
            if stored and not stored.revoked:
                self.refresh_tokens.revoke(stored)

        self.audit.record(
            action="user.logout",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()

    def change_password(
        self,
        user: User,
        *,
        current_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect", code="invalid_password")
        if current_password == new_password:
            raise ValidationAppError(
                "New password must be different from current password",
                code="password_unchanged",
            )

        user.hashed_password = hash_password(new_password)
        self.refresh_tokens.revoke_all_for_user(user.id)
        self.audit.record(
            action="user.change_password",
            user_id=user.id,
            organization_id=user.default_organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()

    def forgot_password(self, email: str) -> None:
        user = self.users.get_by_email(email)
        # Always succeed to avoid email enumeration
        if user is None:
            return

        raw = generate_url_safe_token()
        token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_opaque_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.reset_tokens.add(token)
        self.email.send_password_reset(to=user.email, token=raw)
        self.db.commit()

    def reset_password(self, *, token: str, new_password: str) -> None:
        token_hash = hash_opaque_token(token)
        stored = self.reset_tokens.get_valid_by_hash(token_hash)
        if stored is None:
            raise ValidationAppError("Invalid or expired reset token", code="invalid_reset_token")

        user = self.users.get(stored.user_id)
        if user is None:
            raise ValidationAppError("Invalid or expired reset token", code="invalid_reset_token")

        user.hashed_password = hash_password(new_password)
        stored.used = True
        self.refresh_tokens.revoke_all_for_user(user.id)
        self.audit.record(
            action="user.reset_password",
            user_id=user.id,
            organization_id=user.default_organization_id,
        )
        self.db.commit()

    def verify_email(self, token: str) -> None:
        token_hash = hash_opaque_token(token)
        stored = self.verify_tokens.get_valid_by_hash(token_hash)
        if stored is None:
            raise ValidationAppError(
                "Invalid or expired verification token",
                code="invalid_verification_token",
            )

        user = self.users.get(stored.user_id)
        if user is None:
            raise ValidationAppError(
                "Invalid or expired verification token",
                code="invalid_verification_token",
            )

        user.is_email_verified = True
        stored.used = True
        self.audit.record(
            action="user.verify_email",
            user_id=user.id,
            organization_id=user.default_organization_id,
        )
        self.db.commit()

    def resend_verification(self, email: str) -> None:
        user = self.users.get_by_email(email)
        if user is None or user.is_email_verified:
            return
        self._issue_email_verification(user)
        self.db.commit()

    def _issue_email_verification(self, user: User) -> str:
        raw = generate_url_safe_token()
        token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_opaque_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        )
        self.verify_tokens.add(token)
        self.email.send_verification(to=user.email, token=raw)
        return raw

    def _roles_for_user(self, user: User, organization_id: Optional[int]) -> list[str]:
        if user.is_superuser:
            return [RoleName.SUPER_ADMIN.value]

        if organization_id is None:
            return []

        memberships = self.memberships.list_for_user_org(user.id, organization_id)
        return [m.role.name for m in memberships if m.role is not None]

    def _issue_token_pair(
        self,
        user: User,
        *,
        organization_id: Optional[int],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenPair:
        roles = self._roles_for_user(user, organization_id)
        claims = {
            "org_id": organization_id,
            "roles": roles,
            "is_superuser": user.is_superuser,
            "email": user.email,
        }
        access = create_access_token(str(user.id), claims=claims)
        refresh, jti, expires_at = create_refresh_token(str(user.id), claims={"org_id": organization_id})

        stored = RefreshToken(
            user_id=user.id,
            jti=jti,
            token_hash=hash_opaque_token(refresh),
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.refresh_tokens.add(stored)

        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
