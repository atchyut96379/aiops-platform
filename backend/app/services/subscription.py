from dataclasses import dataclass

from app.models.enums import SubscriptionPlan


@dataclass(frozen=True)
class PlanLimits:
    max_assets: int
    max_agents: int
    max_alert_rules: int
    max_log_entries: int
    log_retention_days: int
    ai_enabled: bool
    pdf_reports: bool
    excel_reports: bool


PLAN_LIMITS: dict[str, PlanLimits] = {
    SubscriptionPlan.FREE.value: PlanLimits(
        max_assets=10,
        max_agents=2,
        max_alert_rules=10,
        max_log_entries=5000,
        log_retention_days=7,
        ai_enabled=False,
        pdf_reports=False,
        excel_reports=False,
    ),
    SubscriptionPlan.STARTER.value: PlanLimits(
        max_assets=50,
        max_agents=10,
        max_alert_rules=25,
        max_log_entries=50000,
        log_retention_days=30,
        ai_enabled=True,
        pdf_reports=True,
        excel_reports=True,
    ),
    SubscriptionPlan.PROFESSIONAL.value: PlanLimits(
        max_assets=200,
        max_agents=50,
        max_alert_rules=100,
        max_log_entries=500000,
        log_retention_days=90,
        ai_enabled=True,
        pdf_reports=True,
        excel_reports=True,
    ),
    SubscriptionPlan.ENTERPRISE.value: PlanLimits(
        max_assets=10000,
        max_agents=500,
        max_alert_rules=1000,
        max_log_entries=10000000,
        log_retention_days=365,
        ai_enabled=True,
        pdf_reports=True,
        excel_reports=True,
    ),
}


def get_plan_limits(plan: str) -> PlanLimits:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[SubscriptionPlan.FREE.value])
