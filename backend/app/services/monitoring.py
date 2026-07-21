from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.infrastructure_asset import InfrastructureAsset
from app.models.monitoring_metric import MonitoringMetric
from app.models.user import User
from app.repositories.audit import AuditLogRepository
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.monitoring_metric import MonitoringMetricRepository
from app.repositories.role import UserRoleRepository
from app.schemas.monitoring import (
    MonitoringHealthSummary,
    MonitoringMetricCreate,
    MonitoringMetricResponse,
    MonitoringMetricStats,
)
from app.services.infrastructure import InfrastructureService
from app.models.enums import RoleName


class MonitoringService:
    WRITE_ROLES = {
        RoleName.ORGANIZATION_ADMIN.value,
        RoleName.DEVOPS_ENGINEER.value,
        RoleName.CLOUD_ENGINEER.value,
        RoleName.SUPER_ADMIN.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.metrics = MonitoringMetricRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.memberships = UserRoleRepository(db)
        self.audit = AuditLogRepository(db)

    def record_metric(
        self,
        *,
        organization_id: int,
        asset_id: int,
        payload: MonitoringMetricCreate,
        requester: User,
        roles: list[str],
    ) -> MonitoringMetricResponse:
        self._require_write_access(requester, organization_id, roles)
        asset = self._get_asset_or_404(organization_id, asset_id)
        metric = MonitoringMetric(
            organization_id=organization_id,
            asset_id=asset.id,
            metric_type=payload.metric_type,
            metric_value=payload.metric_value,
            unit=payload.unit,
            recorded_at=payload.recorded_at or datetime.now(timezone.utc),
        )
        metric.details = payload.details
        self.metrics.add(metric)
        self.audit.record(
            action="monitoring.metric.recorded",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="monitoring_metric",
            resource_id=str(metric.id),
            details={
                "asset_id": asset.id,
                "metric_type": metric.metric_type,
            },
        )
        self.db.commit()
        self.db.refresh(metric)
        return self._to_response(metric)

    def list_metrics(
        self,
        *,
        organization_id: int,
        asset_id: int,
        requester: User,
        metric_type: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[MonitoringMetricResponse]:
        self._require_org_member(requester, organization_id)
        self._get_asset_or_404(organization_id, asset_id)
        metrics = self.metrics.list_for_asset(
            organization_id=organization_id,
            asset_id=asset_id,
            metric_type=metric_type,
            start_at=start_at,
            end_at=end_at,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(metric) for metric in metrics]

    def get_asset_health(
        self, *, organization_id: int, asset_id: int, requester: User
    ) -> MonitoringHealthSummary:
        self._require_org_member(requester, organization_id)
        asset = self._get_asset_or_404(organization_id, asset_id)
        recent = self.metrics.latest_for_asset(organization_id, asset_id)
        metrics = {
            metric.metric_type: {
                "value": metric.metric_value,
                "unit": metric.unit,
                "recorded_at": metric.recorded_at,
                "details": metric.details,
            }
            for metric in recent
        }
        health = self._compute_health(metrics)
        return MonitoringHealthSummary(
            asset_id=asset.id,
            asset_hostname=asset.hostname,
            status=health["status"],
            message=health["message"],
            metrics=metrics,
        )

    def get_asset_stats(
        self, *, organization_id: int, asset_id: int, requester: User
    ) -> MonitoringMetricStats:
        self._require_org_member(requester, organization_id)
        self._get_asset_or_404(organization_id, asset_id)
        stats = self.metrics.stats_by_asset(organization_id, asset_id)
        return MonitoringMetricStats(count_by_type={row[0]: row[1] for row in stats})

    def _compute_health(self, metrics: dict[str, Any]) -> dict[str, str]:
        status = "healthy"
        message = "Asset metrics are within normal ranges"
        cpu = metrics.get("cpu.percent", {}).get("value")
        memory = metrics.get("memory.percent", {}).get("value")
        if cpu is not None and cpu >= 90:
            status = "critical"
            message = "CPU usage is critically high"
        elif memory is not None and memory >= 90:
            status = "critical"
            message = "Memory usage is critically high"
        elif cpu is not None and cpu >= 75:
            status = "warning"
            message = "CPU usage is elevated"
        elif memory is not None and memory >= 75:
            status = "warning"
            message = "Memory usage is elevated"
        return {"status": status, "message": message}

    def _get_asset_or_404(self, organization_id: int, asset_id: int) -> InfrastructureAsset:
        asset = self.assets.get(asset_id)
        if asset is None or asset.organization_id != organization_id or not asset.is_active:
            raise NotFoundError("Infrastructure asset not found")
        return asset

    def _require_org_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")

    def _require_write_access(self, user: User, organization_id: int, roles: list[str]) -> None:
        self._require_org_member(user, organization_id)
        if user.is_superuser or RoleName.SUPER_ADMIN.value in roles:
            return
        if not self.WRITE_ROLES.intersection(roles):
            raise ForbiddenError("Insufficient permissions to record monitoring metrics")

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
