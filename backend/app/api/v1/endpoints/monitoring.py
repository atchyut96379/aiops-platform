from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession, get_client_meta
from app.schemas.monitoring import (
    MonitoringHealthSummary,
    MonitoringMetricCreate,
    MonitoringMetricResponse,
    MonitoringMetricStats,
)
from app.security.rbac import require_any_authenticated, require_roles
from app.services.monitoring import MonitoringService
from app.models.enums import RoleName

router = APIRouter(prefix="/organizations/me/monitoring", tags=["Monitoring"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.post(
    "/assets/{asset_id}/metrics",
    response_model=MonitoringMetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a monitoring metric for an asset",
)
def record_metric(
    request: Request,
    asset_id: int,
    payload: MonitoringMetricCreate,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.DEVOPS_ENGINEER,
        RoleName.CLOUD_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> MonitoringMetricResponse:
    ip, ua = get_client_meta(request)
    return MonitoringService(db).record_metric(
        organization_id=_org_id(current),
        asset_id=asset_id,
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.get(
    "/assets/{asset_id}/metrics",
    response_model=list[MonitoringMetricResponse],
    summary="List metrics for an asset",
)
def list_metrics(
    asset_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
    metric_type: Optional[str] = Query(default=None, max_length=100),
    start_at: Optional[datetime] = Query(default=None),
    end_at: Optional[datetime] = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[MonitoringMetricResponse]:
    return MonitoringService(db).list_metrics(
        organization_id=_org_id(current),
        asset_id=asset_id,
        requester=current.user,
        metric_type=metric_type,
        start_at=start_at,
        end_at=end_at,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/assets/{asset_id}/health",
    response_model=MonitoringHealthSummary,
    summary="Get health summary for an asset",
)
def asset_health(
    asset_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> MonitoringHealthSummary:
    return MonitoringService(db).get_asset_health(
        organization_id=_org_id(current),
        asset_id=asset_id,
        requester=current.user,
    )


@router.get(
    "/assets/{asset_id}/stats",
    response_model=MonitoringMetricStats,
    summary="Get metric counts for an asset",
)
def asset_stats(
    asset_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> MonitoringMetricStats:
    return MonitoringService(db).get_asset_stats(
        organization_id=_org_id(current),
        asset_id=asset_id,
        requester=current.user,
    )
