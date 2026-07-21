from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.alert import Alert
from app.models.enums import IncidentSeverity, IncidentStatus, RoleName
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.monitoring_metric import MonitoringMetricRepository
from app.repositories.user import UserRepository
from app.schemas.incident import IncidentCreate
from app.services.incident import IncidentService
from app.services.notification import NotificationDispatchService


class AlertingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.alerts = AlertRepository(db)
        self.metrics = MonitoringMetricRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.users = UserRepository(db)
        self.incident_service = IncidentService(db)
        self.notifications = NotificationDispatchService(db)

    def evaluate_metric_and_alert(
        self, organization_id: int, metric: Any, requester_id: int
    ) -> None:
        """Evaluate a metric and create an alert (and incident) when thresholds exceeded."""
        metric_type = metric.metric_type
        value = metric.metric_value
        asset_id = metric.asset_id

        level: Optional[str] = None
        if metric_type == "cpu.percent":
            if value is None:
                return
            if value >= 90:
                level = "critical"
            elif value >= 75:
                level = "warning"
            else:
                return
        elif metric_type == "memory.percent":
            if value is None:
                return
            if value >= 90:
                level = "critical"
            elif value >= 75:
                level = "warning"
            else:
                return
        else:
            return

        alert = Alert(
            organization_id=organization_id,
            asset_id=asset_id,
            alert_type=metric_type,
            level=level,
        )
        alert.details = {"metric_value": value}
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
            requester = self.users.get(requester_id)
            if requester is not None:
                try:
                    incident = self.incident_service.create_incident(
                        organization_id=organization_id,
                        payload=IncidentCreate(
                            asset_id=asset_id,
                            incident_type="auto_alert",
                            title=f"Auto incident: {metric_type} {value}",
                            description=(
                                f"Auto-generated incident from alert: {metric_type}={value}"
                            ),
                            severity=IncidentSeverity.CRITICAL,
                            details={"metric_value": value, "alert_id": alert.id},
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
