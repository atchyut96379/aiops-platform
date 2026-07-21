from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import AssetStatus, AssetType, EnvironmentType, RoleName
from app.schemas.infrastructure import (
    InfrastructureAssetCreate,
    InfrastructureAssetResponse,
    InfrastructureAssetStats,
    InfrastructureAssetUpdate,
)
from app.security.rbac import require_any_authenticated
from app.services.infrastructure import InfrastructureService

router = APIRouter(prefix="/organizations/me/assets", tags=["Infrastructure"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("/stats", response_model=InfrastructureAssetStats, summary="Asset inventory stats")
def asset_stats(db: DbSession, current: AuthenticatedUser) -> InfrastructureAssetStats:
    return InfrastructureService(db).get_stats(
        organization_id=_org_id(current),
        requester=current.user,
    )


@router.get("", response_model=list[InfrastructureAssetResponse], summary="List infrastructure assets")
def list_assets(
    db: DbSession,
    current: AuthenticatedUser,
    asset_type: AssetType | None = Query(default=None),
    environment: EnvironmentType | None = Query(default=None),
    status: AssetStatus | None = Query(default=None),
    project_id: int | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[InfrastructureAssetResponse]:
    return InfrastructureService(db).list_assets(
        organization_id=_org_id(current),
        requester=current.user,
        asset_type=asset_type.value if asset_type else None,
        environment=environment.value if environment else None,
        status=status.value if status else None,
        project_id=project_id,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=InfrastructureAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register infrastructure asset",
)
def create_asset(
    payload: InfrastructureAssetCreate,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> InfrastructureAssetResponse:
    return InfrastructureService(db).create_asset(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.get("/{asset_id}", response_model=InfrastructureAssetResponse, summary="Get infrastructure asset")
def get_asset(
    asset_id: int, db: DbSession, current: AuthenticatedUser
) -> InfrastructureAssetResponse:
    return InfrastructureService(db).get_asset(
        organization_id=_org_id(current),
        asset_id=asset_id,
        requester=current.user,
    )


@router.patch("/{asset_id}", response_model=InfrastructureAssetResponse, summary="Update infrastructure asset")
def update_asset(
    asset_id: int,
    payload: InfrastructureAssetUpdate,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> InfrastructureAssetResponse:
    return InfrastructureService(db).update_asset(
        organization_id=_org_id(current),
        asset_id=asset_id,
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete infrastructure asset")
def delete_asset(
    asset_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> None:
    InfrastructureService(db).delete_asset(
        organization_id=_org_id(current),
        asset_id=asset_id,
        requester=current.user,
        roles=current.roles,
    )
