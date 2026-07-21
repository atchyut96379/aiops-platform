from typing import Any

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.repositories.alert import AlertRepository
from app.repositories.monitoring_metric import MonitoringMetricRepository
from app.services.incident import IncidentService
from app.models.enums import RoleName
from app.core.exceptions import NotFoundError, ForbiddenError
from datetime import datetime


class AlertingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.alerts = AlertRepository(db)
        self.metrics = MonitoringMetricRepository(db)
        self.incident_service = IncidentService(db)

    def evaluate_metric_and_alert(self, organization_id: int, metric: Any, requester_id: int) -> None:
        """Evaluate a metric and create an alert (and incident) when thresholds exceeded.

        This is intentionally simple and rule-based for MVP.
        """
        metric_type = metric.metric_type
        value = metric.metric_value
        asset_id = metric.asset_id

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

        # Debug: surface alert creation path during tests
        try:
            pass
        except Exception:
            pass

        alert = Alert(
            organization_id=organization_id,
            asset_id=asset_id,
            alert_type=metric_type,
            level=level,
        )
        alert.details = {"metric_value": value}
        self.alerts.add(alert)
        self.db.commit()

        # For critical alerts, auto-create an incident to kick off response.
        if level == "critical":
            try:
                self.incident_service.create_incident(
                    organization_id=organization_id,
                    payload=type("P", (), {
                        "asset_id": asset_id,
                        "incident_type": "auto_alert",
                        "title": f"Auto incident: {metric_type} {value}",
                        "description": f"Auto-generated incident from alert: {metric_type}={value}",
                        "severity": type("S", (), {"value": "critical"}),
                        "details": {"metric_value": value},
                    })(),
                    requester=self._fake_user(requester_id),
                )
            except Exception:
                # Fail-safe: do not block metric recording on incident errors
                pass

    def _fake_user(self, user_id: int):
        # Lightweight User-like object for incident service calls
        class U:
            def __init__(self, id: int):
                self.id = id
                self.is_superuser = False

        return U(user_id)

    def acknowledge_alert(self, organization_id: int, alert_id: int, requester) -> Alert:
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

    def resolve_alert(self, organization_id: int, alert_id: int, requester) -> Alert:
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
