from fastapi import APIRouter, Depends

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.organization import OrganizationResponse, OrganizationUpdate
from app.security.rbac import require_roles
from app.services.organization import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


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
