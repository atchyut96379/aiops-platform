from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.dashboard import DashboardSummary, DashboardTrends
from app.security.rbac import require_any_authenticated, require_roles
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/organizations/me", tags=["Dashboard"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("/dashboard", response_model=DashboardSummary, summary="Organization dashboard summary")
def dashboard_summary(db: DbSession, current: AuthenticatedUser) -> DashboardSummary:
    return DashboardService(db).get_summary(
        organization_id=_org_id(current), requester=current.user
    )


@router.get("/dashboard/trends", response_model=DashboardTrends, summary="Dashboard trends")
def dashboard_trends(
    db: DbSession,
    current: AuthenticatedUser,
    days: int = Query(7, ge=1, le=90),
) -> DashboardTrends:
    return DashboardService(db).get_trends(
        organization_id=_org_id(current), requester=current.user, days=days
    )


@router.get(
    "/reports/incidents",
    response_class=PlainTextResponse,
    summary="Export incidents CSV report",
)
def export_incidents_report(
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> PlainTextResponse:
    csv_data = DashboardService(db).export_incidents_csv(
        organization_id=_org_id(current), requester=current.user
    )
    return PlainTextResponse(csv_data, media_type="text/csv")
