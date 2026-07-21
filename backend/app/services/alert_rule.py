from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.alert_rule import AlertRule
from app.models.enums import RoleName
from app.models.user import User
from app.repositories.alert_rule import AlertRuleRepository
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.role import UserRoleRepository
from app.schemas.alert_rule import AlertRuleCreate, AlertRuleResponse, AlertRuleUpdate
from app.services.subscription import get_plan_limits

DEFAULT_RULES = [
    {
        "name": "CPU warning",
        "metric_type": "cpu.percent",
        "operator": "gte",
        "threshold": 75.0,
        "level": "warning",
    },
    {
        "name": "CPU critical",
        "metric_type": "cpu.percent",
        "operator": "gte",
        "threshold": 90.0,
        "level": "critical",
    },
    {
        "name": "Memory warning",
        "metric_type": "memory.percent",
        "operator": "gte",
        "threshold": 75.0,
        "level": "warning",
    },
    {
        "name": "Memory critical",
        "metric_type": "memory.percent",
        "operator": "gte",
        "threshold": 90.0,
        "level": "critical",
    },
    {
        "name": "Disk warning",
        "metric_type": "disk.percent",
        "operator": "gte",
        "threshold": 80.0,
        "level": "warning",
    },
]


class AlertRuleService:
    WRITE_ROLES = {
        RoleName.ORGANIZATION_ADMIN.value,
        RoleName.DEVOPS_ENGINEER.value,
        RoleName.SUPER_ADMIN.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.rules = AlertRuleRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.orgs = OrganizationRepository(db)
        self.memberships = UserRoleRepository(db)

    def seed_default_rules(self, organization_id: int) -> None:
        if self.rules.count_for_organization(organization_id) > 0:
            return
        for rule_data in DEFAULT_RULES:
            rule = AlertRule(organization_id=organization_id, **rule_data)
            self.rules.add(rule)
        self.db.commit()

    def list_rules(
        self,
        *,
        organization_id: int,
        requester: User,
        asset_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> list[AlertRuleResponse]:
        self._require_member(requester, organization_id)
        self.seed_default_rules(organization_id)
        rules = self.rules.list_for_organization(
            organization_id, asset_id=asset_id, skip=skip, limit=limit
        )
        return [AlertRuleResponse.model_validate(r) for r in rules]

    def create_rule(
        self,
        *,
        organization_id: int,
        payload: AlertRuleCreate,
        requester: User,
        roles: list[str],
    ) -> AlertRuleResponse:
        self._require_write_access(requester, organization_id, roles)
        org = self.orgs.get(organization_id)
        if org is None:
            raise NotFoundError("Organization not found")

        limits = get_plan_limits(org.subscription_plan)
        if self.rules.count_for_organization(organization_id) >= limits.max_alert_rules:
            raise ValidationAppError(
                f"Alert rule limit reached for {org.subscription_plan} plan"
            )

        if payload.asset_id is not None:
            asset = self.assets.get(payload.asset_id)
            if asset is None or asset.organization_id != organization_id:
                raise NotFoundError("Asset not found")

        rule = AlertRule(
            organization_id=organization_id,
            asset_id=payload.asset_id,
            name=payload.name.strip(),
            metric_type=payload.metric_type,
            operator=payload.operator,
            threshold=payload.threshold,
            level=payload.level,
            enabled=payload.enabled,
            cooldown_minutes=payload.cooldown_minutes,
            description=payload.description,
        )
        self.rules.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return AlertRuleResponse.model_validate(rule)

    def update_rule(
        self,
        *,
        organization_id: int,
        rule_id: int,
        payload: AlertRuleUpdate,
        requester: User,
        roles: list[str],
    ) -> AlertRuleResponse:
        self._require_write_access(requester, organization_id, roles)
        rule = self.rules.get(rule_id)
        if rule is None or rule.organization_id != organization_id:
            raise NotFoundError("Alert rule not found")

        updates = payload.model_dump(exclude_unset=True)
        if "asset_id" in updates and updates["asset_id"] is not None:
            asset = self.assets.get(updates["asset_id"])
            if asset is None or asset.organization_id != organization_id:
                raise NotFoundError("Asset not found")

        for key, value in updates.items():
            setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return AlertRuleResponse.model_validate(rule)

    def delete_rule(
        self, *, organization_id: int, rule_id: int, requester: User, roles: list[str]
    ) -> None:
        self._require_write_access(requester, organization_id, roles)
        rule = self.rules.get(rule_id)
        if rule is None or rule.organization_id != organization_id:
            raise NotFoundError("Alert rule not found")
        self.rules.delete(rule)
        self.db.commit()

    def _require_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")

    def _require_write_access(self, user: User, organization_id: int, roles: list[str]) -> None:
        self._require_member(user, organization_id)
        if user.is_superuser or RoleName.SUPER_ADMIN.value in roles:
            return
        if not self.WRITE_ROLES.intersection(roles):
            raise ForbiddenError("Insufficient permissions to manage alert rules")
