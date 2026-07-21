from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.integration import (
    CloudIntegrationCreate,
    CloudIntegrationResponse,
    CloudSyncResult,
)
from app.security.rbac import require_any_authenticated, require_roles
from app.services.cloud_integration import CloudIntegrationService

router = APIRouter(prefix="/organizations/me/integrations", tags=["Cloud Integrations"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("", response_model=list[CloudIntegrationResponse], summary="List cloud integrations")
def list_integrations(db: DbSession, current: AuthenticatedUser) -> list[CloudIntegrationResponse]:
    return CloudIntegrationService(db).list_integrations(
        organization_id=_org_id(current), requester=current.user
    )


@router.post(
    "",
    response_model=CloudIntegrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Connect cloud provider",
)
def create_integration(
    payload: CloudIntegrationCreate,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.CLOUD_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> CloudIntegrationResponse:
    return CloudIntegrationService(db).create_integration(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.post(
    "/{integration_id}/sync",
    response_model=CloudSyncResult,
    summary="Sync assets from cloud provider",
)
def sync_integration(
    integration_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.CLOUD_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> CloudSyncResult:
    return CloudIntegrationService(db).sync_integration(
        organization_id=_org_id(current),
        integration_id=integration_id,
        requester=current.user,
        roles=current.roles,
    )
