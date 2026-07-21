from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import CurrentUser, DbSession
from app.schemas.alert import AlertResponse
from app.security.rbac import require_any_authenticated
from app.services.alerting import AlertingService

router = APIRouter(prefix="/organizations/me/alerts", tags=["Alerts"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("", response_model=list[AlertResponse], summary="List alerts")
def list_alerts(
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
    asset_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    level: Optional[str] = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[AlertResponse]:
    svc = AlertingService(db)
    alerts = svc.alerts.list_for_organization(
        organization_id=_org_id(current),
        asset_id=asset_id,
        status=status,
        level=level,
        skip=skip,
        limit=limit,
    )
    return [
        AlertResponse(
            id=a.id,
            organization_id=a.organization_id,
            asset_id=a.asset_id,
            alert_type=a.alert_type,
            level=a.level,
            status=a.status,
            details=a.details,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in alerts
    ]


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse, summary="Acknowledge an alert")
def acknowledge_alert(
    alert_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> AlertResponse:
    svc = AlertingService(db)
    alert = svc.acknowledge_alert(organization_id=_org_id(current), alert_id=alert_id, requester=current)
    return AlertResponse(
        id=alert.id,
        organization_id=alert.organization_id,
        asset_id=alert.asset_id,
        alert_type=alert.alert_type,
        level=alert.level,
        status=alert.status,
        details=alert.details,
        acknowledged=bool(alert.acknowledged),
        acknowledged_at=alert.acknowledged_at,
        acknowledged_by_id=alert.acknowledged_by_id,
        resolved=bool(alert.resolved),
        resolved_at=alert.resolved_at,
        resolved_by_id=alert.resolved_by_id,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


@router.post("/{alert_id}/resolve", response_model=AlertResponse, summary="Resolve an alert")
def resolve_alert(
    alert_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> AlertResponse:
    svc = AlertingService(db)
    alert = svc.resolve_alert(organization_id=_org_id(current), alert_id=alert_id, requester=current)
    return AlertResponse(
        id=alert.id,
        organization_id=alert.organization_id,
        asset_id=alert.asset_id,
        alert_type=alert.alert_type,
        level=alert.level,
        status=alert.status,
        details=alert.details,
        acknowledged=bool(alert.acknowledged),
        acknowledged_at=alert.acknowledged_at,
        acknowledged_by_id=alert.acknowledged_by_id,
        resolved=bool(alert.resolved),
        resolved_at=alert.resolved_at,
        resolved_by_id=alert.resolved_by_id,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )
