from fastapi import APIRouter, Depends, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.membership import (
    MemberRolesUpdate,
    OrganizationInviteCreate,
    OrganizationInviteResponse,
    OrganizationMemberResponse,
)
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from app.security.rbac import require_roles
from app.services.membership import MembershipService
from app.services.organization import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _invite_response(invite) -> OrganizationInviteResponse:
    return OrganizationInviteResponse(
        id=invite.id,
        organization_id=invite.organization_id,
        email=invite.email,
        role_name=invite.role.name if invite.role else "",
        status=invite.status,
        invited_by_user_id=invite.invited_by_user_id,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
        accepted_at=invite.accepted_at,
    )


@router.get("", response_model=list[OrganizationResponse], summary="List user's organizations")
def list_organizations(
    db: DbSession, current: AuthenticatedUser
) -> list[OrganizationResponse]:
    orgs = MembershipService(db).list_user_organizations(current.user)
    return [OrganizationResponse.model_validate(org) for org in orgs]


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
def create_organization(
    payload: OrganizationCreate,
    db: DbSession,
    current: AuthenticatedUser,
) -> OrganizationResponse:
    org = MembershipService(db).create_organization(current.user, payload)
    return OrganizationResponse.model_validate(org)


@router.get("/me", response_model=OrganizationResponse, summary="Get current organization")
def get_my_organization(db: DbSession, current: AuthenticatedUser) -> OrganizationResponse:
    org = OrganizationService(db).get_for_user(current.user, current.organization_id)
    return OrganizationResponse.model_validate(org)


@router.patch(
    "/me",
    response_model=OrganizationResponse,
    summary="Update current organization",
)
def update_my_organization(
    payload: OrganizationUpdate,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> OrganizationResponse:
    org = OrganizationService(db).update(current.user, payload, current.organization_id)
    return OrganizationResponse.model_validate(org)


@router.get("/me/members", response_model=list[OrganizationMemberResponse], summary="List org members")
def list_members(
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> list[OrganizationMemberResponse]:
    org_id = current.organization_id
    if org_id is None:
        return []
    return MembershipService(db).list_members(organization_id=org_id, requester=current.user)


@router.patch(
    "/me/members/{user_id}/roles",
    response_model=OrganizationMemberResponse,
    summary="Update member roles",
)
def update_member_roles(
    user_id: int,
    payload: MemberRolesUpdate,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> OrganizationMemberResponse:
    org_id = current.organization_id
    if org_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return MembershipService(db).update_member_roles(
        organization_id=org_id,
        user_id=user_id,
        payload=payload,
        requester=current.user,
    )


@router.delete(
    "/me/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove organization member",
)
def remove_member(
    user_id: int,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> None:
    org_id = current.organization_id
    if org_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    MembershipService(db).remove_member(
        organization_id=org_id, user_id=user_id, requester=current.user
    )


@router.post(
    "/me/invites",
    response_model=OrganizationInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite user to organization",
)
def create_invite(
    payload: OrganizationInviteCreate,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> OrganizationInviteResponse:
    org_id = current.organization_id
    if org_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    invite = MembershipService(db).create_invite(
        organization_id=org_id, payload=payload, requester=current.user
    )
    return _invite_response(invite)


@router.get("/me/invites", response_model=list[OrganizationInviteResponse], summary="List invites")
def list_invites(
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> list[OrganizationInviteResponse]:
    org_id = current.organization_id
    if org_id is None:
        return []
    invites = MembershipService(db).list_invites(organization_id=org_id, requester=current.user)
    return [_invite_response(invite) for invite in invites]


@router.delete(
    "/me/invites/{invite_id}",
    response_model=OrganizationInviteResponse,
    summary="Revoke organization invite",
)
def revoke_invite(
    invite_id: int,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> OrganizationInviteResponse:
    org_id = current.organization_id
    if org_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    invite = MembershipService(db).revoke_invite(
        organization_id=org_id, invite_id=invite_id, requester=current.user
    )
    return _invite_response(invite)
