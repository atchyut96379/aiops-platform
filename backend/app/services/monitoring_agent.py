import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.core.security import hash_opaque_token
from app.models.enums import RoleName
from app.models.monitoring_agent import MonitoringAgent
from app.models.user import User
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.monitoring_agent import MonitoringAgentRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.role import UserRoleRepository
from app.schemas.monitoring_agent import (
    AgentHeartbeatRequest,
    AgentLogsIngestRequest,
    AgentMetricsIngestRequest,
    MonitoringAgentCreate,
    MonitoringAgentCreatedResponse,
    MonitoringAgentResponse,
)
from app.services.log_collection import LogCollectionService
from app.services.monitoring import MonitoringService
from app.services.subscription import get_plan_limits
from app.schemas.monitoring import MonitoringMetricCreate


class MonitoringAgentService:
    WRITE_ROLES = {
        RoleName.ORGANIZATION_ADMIN.value,
        RoleName.DEVOPS_ENGINEER.value,
        RoleName.CLOUD_ENGINEER.value,
        RoleName.SUPER_ADMIN.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.agents = MonitoringAgentRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.orgs = OrganizationRepository(db)
        self.memberships = UserRoleRepository(db)

    def create_agent(
        self,
        *,
        organization_id: int,
        payload: MonitoringAgentCreate,
        requester: User,
        roles: list[str],
    ) -> MonitoringAgentCreatedResponse:
        self._require_write_access(requester, organization_id, roles)
        org = self.orgs.get(organization_id)
        if org is None:
            raise NotFoundError("Organization not found")

        limits = get_plan_limits(org.subscription_plan)
        if self.agents.count_for_organization(organization_id) >= limits.max_agents:
            raise ValidationAppError(
                f"Agent limit reached for {org.subscription_plan} plan ({limits.max_agents})"
            )

        if payload.asset_id is not None:
            asset = self.assets.get(payload.asset_id)
            if asset is None or asset.organization_id != organization_id:
                raise NotFoundError("Asset not found")

        api_key = f"aiops_{secrets.token_urlsafe(32)}"
        agent = MonitoringAgent(
            organization_id=organization_id,
            asset_id=payload.asset_id,
            name=payload.name.strip(),
            hostname=payload.hostname,
            api_key_hash=hash_opaque_token(api_key),
            api_key_prefix=api_key[:12],
        )
        self.agents.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        base = MonitoringAgentResponse.model_validate(agent)
        return MonitoringAgentCreatedResponse(**base.model_dump(), api_key=api_key)

    def list_agents(
        self, *, organization_id: int, requester: User, skip: int = 0, limit: int = 100
    ) -> list[MonitoringAgentResponse]:
        self._require_member(requester, organization_id)
        agents = self.agents.list_for_organization(organization_id, skip=skip, limit=limit)
        return [MonitoringAgentResponse.model_validate(a) for a in agents]

    def revoke_agent(
        self, *, organization_id: int, agent_id: int, requester: User, roles: list[str]
    ) -> MonitoringAgentResponse:
        self._require_write_access(requester, organization_id, roles)
        agent = self.agents.get(agent_id)
        if agent is None or agent.organization_id != organization_id:
            raise NotFoundError("Agent not found")
        agent.is_active = False
        self.db.commit()
        self.db.refresh(agent)
        return MonitoringAgentResponse.model_validate(agent)

    def record_heartbeat(
        self, agent: MonitoringAgent, payload: AgentHeartbeatRequest
    ) -> MonitoringAgentResponse:
        agent.last_heartbeat_at = datetime.now(timezone.utc)
        if payload.agent_version:
            agent.agent_version = payload.agent_version
        if payload.hostname:
            agent.hostname = payload.hostname
        self.db.commit()
        self.db.refresh(agent)
        return MonitoringAgentResponse.model_validate(agent)

    def ingest_metrics(
        self, agent: MonitoringAgent, payload: AgentMetricsIngestRequest
    ) -> dict[str, int]:
        if agent.asset_id is None:
            raise ValidationAppError("Agent is not linked to an asset")

        monitoring = MonitoringService(self.db)
        count = 0
        for item in payload.metrics:
            monitoring.record_metric_from_agent(
                organization_id=agent.organization_id,
                asset_id=agent.asset_id,
                payload=MonitoringMetricCreate(
                    metric_type=item.metric_type,
                    metric_value=item.metric_value,
                    unit=item.unit,
                    recorded_at=item.recorded_at,
                ),
            )
            count += 1
        return {"ingested": count}

    def ingest_logs(self, agent: MonitoringAgent, payload: AgentLogsIngestRequest) -> dict[str, int]:
        logs_service = LogCollectionService(self.db)
        return logs_service.ingest_from_agent(
            organization_id=agent.organization_id,
            asset_id=agent.asset_id,
            payload=payload,
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
            raise ForbiddenError("Insufficient permissions to manage monitoring agents")
