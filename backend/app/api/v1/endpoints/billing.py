from fastapi import APIRouter, Request

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.schemas.auth import BillingCheckoutRequest, BillingCheckoutResponse
from app.services.stripe_billing import StripeBillingService
from app.services.subscription import PLAN_LIMITS, get_plan_limits

router = APIRouter(prefix="/organizations/me/billing", tags=["Billing"])
webhook_router = APIRouter(prefix="/billing", tags=["Billing"])


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
        "stripe_configured": bool(org.stripe_customer_id),
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


@router.post(
    "/checkout",
    response_model=BillingCheckoutResponse,
    summary="Start Stripe checkout or demo upgrade",
)
def checkout(
    payload: BillingCheckoutRequest,
    db: DbSession,
    current: AuthenticatedUser,
) -> BillingCheckoutResponse:
    result = StripeBillingService(db).create_checkout(
        organization_id=_org_id(current),
        plan=payload.plan,
        requester=current.user,
        roles=current.roles,
    )
    return BillingCheckoutResponse(**result)


@webhook_router.post("/webhook", summary="Stripe webhook handler")
async def stripe_webhook(request: Request, db: DbSession) -> dict:
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    return StripeBillingService(db).handle_webhook(payload, signature)
