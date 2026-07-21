from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.incident import Incident
from app.models.infrastructure_asset import InfrastructureAsset
from app.models.monitoring_metric import MonitoringMetric
from app.models.user import User
from app.repositories.role import UserRoleRepository
from app.core.exceptions import ForbiddenError
from app.schemas.dashboard import DashboardSummary, DashboardTrends


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.memberships = UserRoleRepository(db)

    def get_summary(self, *, organization_id: int, requester: User) -> DashboardSummary:
        self._require_member(requester, organization_id)

        total_assets = self.db.scalar(
            select(func.count())
            .select_from(InfrastructureAsset)
            .where(
                InfrastructureAsset.organization_id == organization_id,
                InfrastructureAsset.is_active.is_(True),
            )
        ) or 0

        healthy_assets = self.db.scalar(
            select(func.count())
            .select_from(InfrastructureAsset)
            .where(
                InfrastructureAsset.organization_id == organization_id,
                InfrastructureAsset.is_active.is_(True),
                InfrastructureAsset.status == "healthy",
            )
        ) or 0

        open_alerts = self.db.scalar(
            select(func.count())
            .select_from(Alert)
            .where(
                Alert.organization_id == organization_id,
                Alert.resolved.is_(False),
            )
        ) or 0

        critical_alerts = self.db.scalar(
            select(func.count())
            .select_from(Alert)
            .where(
                Alert.organization_id == organization_id,
                Alert.resolved.is_(False),
                Alert.level == "critical",
            )
        ) or 0

        open_incidents = self.db.scalar(
            select(func.count())
            .select_from(Incident)
            .where(
                Incident.organization_id == organization_id,
                Incident.status.in_(["open", "assigned", "investigating", "in_progress"]),
            )
        ) or 0

        closed_incidents = self.db.scalar(
            select(func.count())
            .select_from(Incident)
            .where(
                Incident.organization_id == organization_id,
                Incident.status.in_(["resolved", "closed"]),
            )
        ) or 0

        alerts_by_level = dict(
            self.db.execute(
                select(Alert.level, func.count())
                .where(Alert.organization_id == organization_id, Alert.resolved.is_(False))
                .group_by(Alert.level)
            ).all()
        )

        incidents_by_severity = dict(
            self.db.execute(
                select(Incident.severity, func.count())
                .where(
                    Incident.organization_id == organization_id,
                    Incident.status.in_(["open", "assigned", "investigating", "in_progress"]),
                )
                .group_by(Incident.severity)
            ).all()
        )

        assets_by_status = dict(
            self.db.execute(
                select(InfrastructureAsset.status, func.count())
                .where(
                    InfrastructureAsset.organization_id == organization_id,
                    InfrastructureAsset.is_active.is_(True),
                )
                .group_by(InfrastructureAsset.status)
            ).all()
        )

        return DashboardSummary(
            total_assets=total_assets,
            healthy_assets=healthy_assets,
            open_alerts=open_alerts,
            critical_alerts=critical_alerts,
            open_incidents=open_incidents,
            closed_incidents=closed_incidents,
            alerts_by_level=alerts_by_level,
            incidents_by_severity=incidents_by_severity,
            assets_by_status=assets_by_status,
        )

    def get_trends(self, *, organization_id: int, requester: User, days: int = 7) -> DashboardTrends:
        self._require_member(requester, organization_id)
        since = datetime.now(timezone.utc) - timedelta(days=days)

        alert_rows = self.db.execute(
            select(func.date(Alert.created_at), func.count())
            .where(Alert.organization_id == organization_id, Alert.created_at >= since)
            .group_by(func.date(Alert.created_at))
            .order_by(func.date(Alert.created_at))
        ).all()

        incident_rows = self.db.execute(
            select(func.date(Incident.created_at), func.count())
            .where(Incident.organization_id == organization_id, Incident.created_at >= since)
            .group_by(func.date(Incident.created_at))
            .order_by(func.date(Incident.created_at))
        ).all()

        metric_rows = self.db.execute(
            select(func.date(MonitoringMetric.recorded_at), func.count())
            .where(
                MonitoringMetric.organization_id == organization_id,
                MonitoringMetric.recorded_at >= since,
            )
            .group_by(func.date(MonitoringMetric.recorded_at))
            .order_by(func.date(MonitoringMetric.recorded_at))
        ).all()

        return DashboardTrends(
            days=days,
            alerts_by_day={str(r[0]): r[1] for r in alert_rows},
            incidents_by_day={str(r[0]): r[1] for r in incident_rows},
            metrics_by_day={str(r[0]): r[1] for r in metric_rows},
        )

    def export_incidents_csv(self, *, organization_id: int, requester: User) -> str:
        self._require_member(requester, organization_id)
        incidents = self.db.scalars(
            select(Incident)
            .where(Incident.organization_id == organization_id)
            .order_by(Incident.created_at.desc())
            .limit(5000)
        ).all()
        lines = ["id,title,severity,status,incident_type,asset_id,created_at"]
        for inc in incidents:
            lines.append(
                f'{inc.id},"{inc.title}",{inc.severity},{inc.status},{inc.incident_type},'
                f'{inc.asset_id or ""},{inc.created_at.isoformat() if inc.created_at else ""}'
            )
        return "\n".join(lines)

    def _require_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")
