from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError, ValidationAppError
from app.models.enums import RoleName, SubscriptionPlan
from app.models.organization import Organization
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.role import UserRoleRepository

PLAN_RANK = {
    SubscriptionPlan.FREE.value: 0,
    SubscriptionPlan.STARTER.value: 1,
    SubscriptionPlan.PROFESSIONAL.value: 2,
    SubscriptionPlan.ENTERPRISE.value: 3,
}


class StripeBillingService:
    ADMIN_ROLES = {RoleName.ORGANIZATION_ADMIN.value, RoleName.SUPER_ADMIN.value}

    def __init__(self, db: Session) -> None:
        self.db = db
        self.orgs = OrganizationRepository(db)
        self.memberships = UserRoleRepository(db)

    def create_checkout(
        self,
        *,
        organization_id: int,
        plan: str,
        requester: User,
        roles: list[str],
    ) -> dict[str, Any]:
        self._require_admin(requester, organization_id, roles)
        if plan not in PLAN_RANK or plan == SubscriptionPlan.FREE.value:
            raise ValidationAppError("Invalid subscription plan for checkout")

        org = self.orgs.get(organization_id)
        if org is None:
            raise ValidationAppError("Organization not found")

        if not settings.stripe_configured:
            org.subscription_plan = plan
            self.db.commit()
            return {
                "mode": "demo",
                "upgraded": True,
                "plan": plan,
                "checkout_url": None,
                "message": f"Plan upgraded to {plan} (demo mode — configure STRIPE_SECRET_KEY for live billing)",
            }

        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        price_id = settings.stripe_price_for_plan(plan)
        if not price_id:
            raise ValidationAppError(f"No Stripe price configured for plan '{plan}'")

        customer_id = org.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                name=org.name,
                metadata={"organization_id": str(org.id)},
            )
            customer_id = customer.id
            org.stripe_customer_id = customer_id
            self.db.flush()

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL}/settings?billing=success",
            cancel_url=f"{settings.FRONTEND_URL}/settings?billing=cancel",
            metadata={"organization_id": str(org.id), "plan": plan},
            subscription_data={"metadata": {"organization_id": str(org.id), "plan": plan}},
        )
        self.db.commit()
        return {
            "mode": "stripe",
            "upgraded": False,
            "plan": plan,
            "checkout_url": session.url,
            "session_id": session.id,
        }

    def handle_webhook(self, payload: bytes, signature: str | None) -> dict[str, Any]:
        if not settings.stripe_configured:
            return {"handled": False, "reason": "stripe_not_configured"}

        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise ValidationAppError("STRIPE_WEBHOOK_SECRET is not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, signature or "", settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as exc:
            raise ValidationAppError("Invalid webhook payload") from exc
        except stripe.error.SignatureVerificationError as exc:
            raise ValidationAppError("Invalid webhook signature") from exc

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            org_id = int(data.get("metadata", {}).get("organization_id", 0))
            plan = data.get("metadata", {}).get("plan")
            subscription_id = data.get("subscription")
            if org_id and plan:
                self._apply_plan(org_id, plan, subscription_id)
            return {"handled": True, "event": event_type, "organization_id": org_id, "plan": plan}

        if event_type in {"customer.subscription.updated", "customer.subscription.created"}:
            org_id = int(data.get("metadata", {}).get("organization_id", 0))
            plan = data.get("metadata", {}).get("plan")
            subscription_id = data.get("id")
            status = data.get("status")
            if org_id and plan and status in {"active", "trialing"}:
                self._apply_plan(org_id, plan, subscription_id)
            return {"handled": True, "event": event_type, "organization_id": org_id, "plan": plan}

        if event_type == "customer.subscription.deleted":
            org_id = int(data.get("metadata", {}).get("organization_id", 0))
            if org_id:
                self._apply_plan(org_id, SubscriptionPlan.FREE.value, None)
            return {"handled": True, "event": event_type, "organization_id": org_id}

        return {"handled": False, "event": event_type}

    def _apply_plan(
        self, organization_id: int, plan: str, subscription_id: str | None
    ) -> Organization | None:
        org = self.orgs.get(organization_id)
        if org is None:
            return None
        org.subscription_plan = plan
        if subscription_id:
            org.stripe_subscription_id = subscription_id
        elif plan == SubscriptionPlan.FREE.value:
            org.stripe_subscription_id = None
        self.db.commit()
        self.db.refresh(org)
        return org

    def _require_admin(self, user: User, organization_id: int, roles: list[str]) -> None:
        if user.is_superuser or RoleName.SUPER_ADMIN.value in roles:
            return
        if not self.ADMIN_ROLES.intersection(roles):
            raise ForbiddenError("Only organization admins can manage billing")
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")
