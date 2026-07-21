import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.enums import RoleName
from app.models.infrastructure_asset import InfrastructureAsset
from app.models.platform_connection import PlatformConnection
from app.models.user import User
from app.repositories.platform_connection import PlatformConnectionRepository
from app.repositories.role import UserRoleRepository
from app.schemas.platform import (
    PlatformCollectResult,
    PlatformConnectionCreate,
    PlatformConnectionResponse,
)
from app.services.collectors.docker_collector import collect_docker_metrics
from app.services.collectors.kubernetes_collector import collect_kubernetes_snapshot


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
        self.db.commit()

        return PlatformCollectResult(
            connection_id=conn.id,
            connection_type=conn.connection_type,
            snapshot=snapshot,
            message=f"Collected {conn.connection_type} metrics for '{conn.name}'",
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
