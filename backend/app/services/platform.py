import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.enums import AssetType, RoleName
from app.models.infrastructure_asset import InfrastructureAsset
from app.models.platform_connection import PlatformConnection
from app.models.user import User
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.platform_connection import PlatformConnectionRepository
from app.repositories.role import UserRoleRepository
from app.schemas.monitoring import MonitoringMetricCreate
from app.schemas.platform import (
    PlatformCollectResult,
    PlatformConnectionCreate,
    PlatformConnectionResponse,
)
from app.services.collectors.docker_collector import collect_docker_metrics
from app.services.collectors.kubernetes_collector import collect_kubernetes_snapshot
from app.services.monitoring import MonitoringService


class PlatformService:
    WRITE_ROLES = {
        RoleName.ORGANIZATION_ADMIN.value,
        RoleName.DEVOPS_ENGINEER.value,
        RoleName.CLOUD_ENGINEER.value,
        RoleName.SUPER_ADMIN.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.connections = PlatformConnectionRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.memberships = UserRoleRepository(db)

    def list_connections(
        self, *, organization_id: int, requester: User, connection_type: str | None = None
    ) -> list[PlatformConnectionResponse]:
        self._require_member(requester, organization_id)
        items = self.connections.list_for_organization(organization_id, connection_type)
        return [PlatformConnectionResponse.model_validate(i) for i in items]

    def create_connection(
        self,
        *,
        organization_id: int,
        payload: PlatformConnectionCreate,
        requester: User,
        roles: list[str],
    ) -> PlatformConnectionResponse:
        self._require_write_access(requester, organization_id, roles)
        if payload.connection_type not in {"docker", "kubernetes"}:
            raise ValidationAppError("connection_type must be docker or kubernetes")

        conn = PlatformConnection(
            organization_id=organization_id,
            connection_type=payload.connection_type,
            name=payload.name.strip(),
            endpoint=payload.endpoint,
        )
        conn.config = payload.config
        self.connections.add(conn)
        self.db.commit()
        self.db.refresh(conn)
        return PlatformConnectionResponse.model_validate(conn)

    def collect(
        self,
        *,
        organization_id: int,
        connection_id: int,
        requester: User,
        roles: list[str],
    ) -> PlatformCollectResult:
        self._require_write_access(requester, organization_id, roles)
        conn = self.connections.get(connection_id)
        if conn is None or conn.organization_id != organization_id:
            raise NotFoundError("Platform connection not found")

        conn.collect_status = "collecting"
        self.db.flush()

        if conn.connection_type == "docker":
            snapshot = collect_docker_metrics(conn.endpoint)
        else:
            snapshot = collect_kubernetes_snapshot(conn.config.get("kubeconfig"))

        conn.collect_status = "completed"
        conn.last_collect_at = datetime.now(timezone.utc)
        conn.config = {**conn.config, "last_snapshot": snapshot}
        asset = self._ensure_connection_asset(conn)
        metrics_recorded = self._ingest_platform_metrics(
            organization_id=organization_id,
            connection=conn,
            asset=asset,
            snapshot=snapshot,
        )
        self.db.commit()

        return PlatformCollectResult(
            connection_id=conn.id,
            connection_type=conn.connection_type,
            snapshot=snapshot,
            message=(
                f"Collected {conn.connection_type} metrics for '{conn.name}' "
                f"({metrics_recorded} monitoring metrics recorded)"
            ),
        )

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
            raise ForbiddenError("Insufficient permissions to manage platform connections")

    def _ensure_connection_asset(self, conn: PlatformConnection) -> InfrastructureAsset:
        if conn.asset_id:
            asset = self.assets.get(conn.asset_id)
            if asset and asset.organization_id == conn.organization_id:
                return asset

        slug = re.sub(r"[^a-z0-9-]+", "-", conn.name.lower()).strip("-") or "platform"
        hostname = f"{conn.connection_type}-{conn.id}-{slug}"[:200]
        existing = self.assets.get_by_hostname(conn.organization_id, hostname)
        if existing:
            conn.asset_id = existing.id
            return existing

        asset_type = (
            AssetType.DOCKER_HOST.value
            if conn.connection_type == "docker"
            else AssetType.KUBERNETES_CLUSTER.value
        )
        asset = InfrastructureAsset(
            organization_id=conn.organization_id,
            asset_type=asset_type,
            hostname=hostname,
            environment="production",
            status="healthy",
        )
        asset.tags_list = ["platform", conn.connection_type]
        asset.metadata_dict = {"platform_connection_id": conn.id, "name": conn.name}
        self.assets.add(asset)
        self.db.flush()
        conn.asset_id = asset.id
        return asset

    def _ingest_platform_metrics(
        self,
        *,
        organization_id: int,
        connection: PlatformConnection,
        asset: InfrastructureAsset,
        snapshot: dict[str, Any],
    ) -> int:
        monitoring = MonitoringService(self.db)
        recorded = 0

        if connection.connection_type == "docker":
            count = snapshot.get("count", 0)
            monitoring.record_metric_from_agent(
                organization_id=organization_id,
                asset_id=asset.id,
                payload=MonitoringMetricCreate(
                    metric_type="platform.container.count",
                    metric_value=float(count),
                    unit="count",
                    details={"connection_id": connection.id},
                ),
            )
            recorded += 1
            for container in snapshot.get("containers", []):
                name = container.get("name", "unknown")
                cpu = container.get("cpu_percent")
                if cpu is not None:
                    monitoring.record_metric_from_agent(
                        organization_id=organization_id,
                        asset_id=asset.id,
                        payload=MonitoringMetricCreate(
                            metric_type="platform.container.cpu",
                            metric_value=float(cpu),
                            unit="percent",
                            details={"container": name, "connection_id": connection.id},
                        ),
                    )
                    recorded += 1
                memory = container.get("memory_percent")
                if memory is not None:
                    monitoring.record_metric_from_agent(
                        organization_id=organization_id,
                        asset_id=asset.id,
                        payload=MonitoringMetricCreate(
                            metric_type="platform.container.memory",
                            metric_value=float(memory),
                            unit="percent",
                            details={"container": name, "connection_id": connection.id},
                        ),
                    )
                    recorded += 1
        else:
            monitoring.record_metric_from_agent(
                organization_id=organization_id,
                asset_id=asset.id,
                payload=MonitoringMetricCreate(
                    metric_type="platform.node.count",
                    metric_value=float(snapshot.get("node_count", 0)),
                    unit="count",
                    details={"connection_id": connection.id},
                ),
            )
            monitoring.record_metric_from_agent(
                organization_id=organization_id,
                asset_id=asset.id,
                payload=MonitoringMetricCreate(
                    metric_type="platform.pod.count",
                    metric_value=float(snapshot.get("pod_count", 0)),
                    unit="count",
                    details={"connection_id": connection.id},
                ),
            )
            recorded += 2
            for pod in snapshot.get("pods", []):
                phase = pod.get("phase", "Unknown")
                monitoring.record_metric_from_agent(
                    organization_id=organization_id,
                    asset_id=asset.id,
                    payload=MonitoringMetricCreate(
                        metric_type="platform.pod.running",
                        metric_value=1.0 if phase == "Running" else 0.0,
                        unit="boolean",
                        details={
                            "pod": pod.get("name"),
                            "namespace": pod.get("namespace"),
                            "phase": phase,
                            "connection_id": connection.id,
                        },
                    ),
                )
                recorded += 1

        return recorded
