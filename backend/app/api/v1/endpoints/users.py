from fastapi import APIRouter, Depends, Query, Request

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession, get_client_meta
from app.models.enums import RoleName
from app.schemas.common import TokenPair
from app.schemas.membership import SwitchOrganizationRequest
from app.schemas.user import UserProfileResponse, UserResponse, UserUpdate
from app.services.membership import MembershipService
from app.security.rbac import require_roles
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfileResponse, summary="Get current user profile")
def get_me(db: DbSession, current: AuthenticatedUser) -> UserProfileResponse:
    return UserService(db).get_profile(current.user)


@router.patch("/me", response_model=UserResponse, summary="Update current user profile")
def update_me(
    payload: UserUpdate, db: DbSession, current: AuthenticatedUser
) -> UserResponse:
    user = UserService(db).update_profile(current.user, payload)
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List users in current organization",
)
def list_users(
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[UserResponse]:
    org_id = current.organization_id
    if org_id is None:
        return []
    users = UserService(db).list_organization_users(
        organization_id=org_id,
        requester=current.user,
        skip=skip,
        limit=limit,
    )
    return [UserResponse.model_validate(u) for u in users]


@router.post(
    "/me/switch-organization",
    response_model=TokenPair,
    summary="Switch active organization and refresh tokens",
)
def switch_organization(
    request: Request,
    payload: SwitchOrganizationRequest,
    db: DbSession,
    current: AuthenticatedUser,
) -> TokenPair:
    ip, ua = get_client_meta(request)
    return MembershipService(db).switch_organization(
        current.user,
        payload.organization_id,
        ip_address=ip,
        user_agent=ua,
    )
