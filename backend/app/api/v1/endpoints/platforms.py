from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.platform import (
    PlatformCollectResult,
    PlatformConnectionCreate,
    PlatformConnectionResponse,
)
from app.security.rbac import require_any_authenticated, require_roles
from app.services.platform import PlatformService

router = APIRouter(prefix="/organizations/me/platforms", tags=["Platform Monitoring"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("", response_model=list[PlatformConnectionResponse], summary="List platform connections")
def list_platforms(
    db: DbSession,
    current: AuthenticatedUser,
    connection_type: str | None = Query(default=None),
) -> list[PlatformConnectionResponse]:
    return PlatformService(db).list_connections(
        organization_id=_org_id(current),
        requester=current.user,
        connection_type=connection_type,
    )


@router.post(
    "",
    response_model=PlatformConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Docker host or Kubernetes cluster",
)
def create_platform(
    payload: PlatformConnectionCreate,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.DEVOPS_ENGINEER,
        RoleName.CLOUD_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> PlatformConnectionResponse:
    return PlatformService(db).create_connection(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.post(
    "/{connection_id}/collect",
    response_model=PlatformCollectResult,
    summary="Collect Docker/Kubernetes metrics snapshot",
)
def collect_platform(
    connection_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.DEVOPS_ENGINEER,
        RoleName.CLOUD_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> PlatformCollectResult:
    return PlatformService(db).collect(
        organization_id=_org_id(current),
        connection_id=connection_id,
        requester=current.user,
        roles=current.roles,
    )
