from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.dashboard import DashboardSummary, DashboardTrends
from app.security.rbac import require_any_authenticated, require_roles
from app.services.dashboard import DashboardService
from app.services.reporting import ReportingService

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


@router.get(
    "/reports/incidents.pdf",
    summary="Export incidents PDF report",
)
def export_incidents_pdf(
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> Response:
    pdf_data = ReportingService(db).export_incidents_pdf(
        organization_id=_org_id(current), requester=current.user
    )
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=incidents.pdf"},
    )


@router.get(
    "/reports/incidents.xlsx",
    summary="Export incidents Excel report",
)
def export_incidents_xlsx(
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> Response:
    xlsx_data = ReportingService(db).export_incidents_xlsx(
        organization_id=_org_id(current), requester=current.user
    )
    return Response(
        content=xlsx_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=incidents.xlsx"},
    )
