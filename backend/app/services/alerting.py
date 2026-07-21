from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.alert import Alert
from app.models.enums import ALERT_LEVEL_RANK, IncidentSeverity, RoleName
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.repositories.alert_rule import AlertRuleRepository
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.monitoring_metric import MonitoringMetricRepository
from app.repositories.user import UserRepository
from app.schemas.incident import IncidentCreate
from app.services.alert_rule import AlertRuleService
from app.services.incident import IncidentService
from app.services.notification import NotificationDispatchService


class AlertingService:
    OPERATORS = {
        "gte": lambda value, threshold: value >= threshold,
        "lte": lambda value, threshold: value <= threshold,
        "gt": lambda value, threshold: value > threshold,
        "lt": lambda value, threshold: value < threshold,
        "eq": lambda value, threshold: value == threshold,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.alerts = AlertRepository(db)
        self.rules = AlertRuleRepository(db)
        self.metrics = MonitoringMetricRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.users = UserRepository(db)
        self.incident_service = IncidentService(db)
        self.notifications = NotificationDispatchService(db)

    def evaluate_metric_and_alert(
        self, organization_id: int, metric: Any, requester_id: int
    ) -> None:
        """Evaluate a metric against configured alert rules and create alerts when triggered."""
        metric_type = metric.metric_type
        value = metric.metric_value
        asset_id = metric.asset_id

        if value is None:
            return

        AlertRuleService(self.db).seed_default_rules(organization_id)
        matching_rules = self.rules.get_matching_rules(
            organization_id, metric_type, asset_id
        )
        if not matching_rules:
            return

        triggered: list[tuple[Any, str]] = []
        for rule in matching_rules:
            op_fn = self.OPERATORS.get(rule.operator)
            if op_fn is None:
                continue
            if not op_fn(value, rule.threshold):
                continue

            since = datetime.now(timezone.utc) - timedelta(minutes=rule.cooldown_minutes)
            if self.rules.get_recent_alert_for_rule(
                organization_id, rule.id, asset_id, since
            ):
                continue

            triggered.append((rule, rule.level))

        if not triggered:
            return

        triggered.sort(key=lambda item: ALERT_LEVEL_RANK.get(item[1], 0), reverse=True)
        rule, level = triggered[0]

        alert = Alert(
            organization_id=organization_id,
            asset_id=asset_id,
            alert_type=metric_type,
            level=level,
        )
        alert.details = {
            "metric_value": value,
            "rule_id": rule.id,
            "rule_name": rule.name,
            "threshold": rule.threshold,
            "operator": rule.operator,
        }
        self.alerts.add(alert)
        self.db.flush()

        asset_hostname: Optional[str] = None
        if asset_id is not None:
            asset = self.assets.get(asset_id)
            asset_hostname = asset.hostname if asset else None

        self.notifications.dispatch_alert(
            organization_id=organization_id,
            alert=alert,
            asset_hostname=asset_hostname,
        )

        if level == "critical":
            requester = self.users.get(requester_id) if requester_id else None
            if requester is None:
                from app.repositories.role import UserRoleRepository

                memberships = UserRoleRepository(self.db).list_for_organization(
                    organization_id
                )
                for membership in memberships:
                    if membership.role and membership.role.name == RoleName.ORGANIZATION_ADMIN.value:
                        requester = membership.user
                        break
            if requester is not None:
                try:
                    incident = self.incident_service.create_incident(
                        organization_id=organization_id,
                        payload=IncidentCreate(
                            asset_id=asset_id,
                            incident_type="auto_alert",
                            title=f"Auto incident: {rule.name} ({metric_type}={value})",
                            description=(
                                f"Auto-generated from rule '{rule.name}': "
                                f"{metric_type} {rule.operator} {rule.threshold}, actual={value}"
                            ),
                            severity=IncidentSeverity.CRITICAL,
                            details={
                                "metric_value": value,
                                "alert_id": alert.id,
                                "rule_id": rule.id,
                            },
                        ),
                        requester=requester,
                    )
                    alert.incident_id = incident.id
                    self.db.flush()
                    self.notifications.dispatch_incident(
                        organization_id=organization_id,
                        incident_id=incident.id,
                        title=incident.title,
                        severity=incident.severity,
                        description=incident.description,
                    )
                except Exception:
                    pass

        self.db.commit()

    def acknowledge_alert(self, organization_id: int, alert_id: int, requester: User) -> Alert:
        alert = self.alerts.get(alert_id)
        if not alert:
            raise NotFoundError("Alert not found")
        if alert.organization_id != organization_id:
            raise ForbiddenError("Alert does not belong to your organization")
        if alert.acknowledged:
            return alert
        self.alerts.mark_acknowledged(alert, by_user_id=requester.id)
        self.db.commit()
        return alert

    def resolve_alert(self, organization_id: int, alert_id: int, requester: User) -> Alert:
        alert = self.alerts.get(alert_id)
        if not alert:
            raise NotFoundError("Alert not found")
        if alert.organization_id != organization_id:
            raise ForbiddenError("Alert does not belong to your organization")
        if alert.resolved:
            return alert
        self.alerts.mark_resolved(alert, by_user_id=requester.id)
        self.db.commit()
        return alert
