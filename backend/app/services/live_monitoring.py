from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.models.monitoring_metric import MonitoringMetric
from app.models.user import User
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.monitoring_metric import MonitoringMetricRepository
from app.repositories.role import UserRoleRepository
from app.schemas.monitoring import MonitoringMetricResponse


class LiveMonitoringService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.metrics = MonitoringMetricRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.memberships = UserRoleRepository(db)

    def get_live_snapshot(
        self,
        *,
        organization_id: int,
        requester: User,
        minutes: int = 15,
        limit: int = 200,
    ) -> dict:
        self._require_member(requester, organization_id)
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        recent = self.metrics.list_for_organization_since(organization_id, since, limit=limit)

        asset_map: dict[int, str] = {}
        for asset in self.assets.list_for_organization(organization_id):
            asset_map[asset.id] = asset.hostname

        by_asset: dict[str, dict[str, Any]] = {}
        for metric in recent:
            key = str(metric.asset_id or 0)
            hostname = asset_map.get(metric.asset_id or 0, "unknown")
            if key not in by_asset:
                by_asset[key] = {
                    "asset_id": metric.asset_id,
                    "hostname": hostname,
                    "metrics": {},
                }
            existing = by_asset[key]["metrics"].get(metric.metric_type)
            if existing is None or (metric.recorded_at and metric.recorded_at > existing.get("recorded_at", datetime.min.replace(tzinfo=timezone.utc))):
                by_asset[key]["metrics"][metric.metric_type] = {
                    "value": metric.metric_value,
                    "unit": metric.unit,
                    "recorded_at": metric.recorded_at.isoformat() if metric.recorded_at else None,
                }

        return {
            "as_of": datetime.now(timezone.utc).isoformat(),
            "window_minutes": minutes,
            "assets": list(by_asset.values()),
            "recent_metrics": [self._to_response(m) for m in recent[:50]],
        }

    def _to_response(self, metric: MonitoringMetric) -> MonitoringMetricResponse:
        return MonitoringMetricResponse(
            id=metric.id,
            organization_id=metric.organization_id,
            asset_id=metric.asset_id,
            metric_type=metric.metric_type,
            metric_value=metric.metric_value,
            unit=metric.unit,
            details=metric.details,
            recorded_at=metric.recorded_at,
            created_at=metric.created_at,
            updated_at=metric.updated_at,
        )

    def _require_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")
