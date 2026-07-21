from fastapi import APIRouter

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.schemas.common import MessageResponse
from app.services.subscription import PLAN_LIMITS, get_plan_limits

router = APIRouter(prefix="/organizations/me/billing", tags=["Billing"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("/plan", summary="Get current subscription plan and limits")
def get_plan(db: DbSession, current: AuthenticatedUser) -> dict:
    from app.repositories.organization import OrganizationRepository

    org = OrganizationRepository(db).get(_org_id(current))
    if org is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Organization not found")

    limits = get_plan_limits(org.subscription_plan)
    return {
        "plan": org.subscription_plan,
        "limits": {
            "max_assets": limits.max_assets,
            "max_agents": limits.max_agents,
            "max_alert_rules": limits.max_alert_rules,
            "max_log_entries": limits.max_log_entries,
            "log_retention_days": limits.log_retention_days,
            "ai_enabled": limits.ai_enabled,
            "pdf_reports": limits.pdf_reports,
            "excel_reports": limits.excel_reports,
        },
        "available_plans": list(PLAN_LIMITS.keys()),
    }


@router.post("/upgrade-request", response_model=MessageResponse, summary="Request plan upgrade")
def request_upgrade(db: DbSession, current: AuthenticatedUser) -> MessageResponse:
    return MessageResponse(
        message="Upgrade request recorded. Contact sales@aiops.local for Stripe billing integration."
    )
