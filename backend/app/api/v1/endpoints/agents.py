from fastapi import APIRouter, Depends, status

from app.api.v1.deps import AgentContext, AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.monitoring_agent import (
    AgentHeartbeatRequest,
    AgentLogsIngestRequest,
    AgentMetricsIngestRequest,
    MonitoringAgentCreate,
    MonitoringAgentCreatedResponse,
    MonitoringAgentResponse,
)
from app.security.rbac import require_any_authenticated, require_roles
from app.services.monitoring_agent import MonitoringAgentService

router = APIRouter(prefix="/organizations/me/agents", tags=["Monitoring Agents"])
agent_router = APIRouter(prefix="/agent", tags=["Agent Ingest"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.post(
    "",
    response_model=MonitoringAgentCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a monitoring agent and receive API key",
)
def create_agent(
    payload: MonitoringAgentCreate,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.DEVOPS_ENGINEER,
        RoleName.CLOUD_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> MonitoringAgentCreatedResponse:
    return MonitoringAgentService(db).create_agent(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.get("", response_model=list[MonitoringAgentResponse], summary="List monitoring agents")
def list_agents(
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> list[MonitoringAgentResponse]:
    return MonitoringAgentService(db).list_agents(
        organization_id=_org_id(current), requester=current.user
    )


@router.delete(
    "/{agent_id}",
    response_model=MonitoringAgentResponse,
    summary="Revoke a monitoring agent",
)
def revoke_agent(
    agent_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.DEVOPS_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> MonitoringAgentResponse:
    return MonitoringAgentService(db).revoke_agent(
        organization_id=_org_id(current),
        agent_id=agent_id,
        requester=current.user,
        roles=current.roles,
    )


@agent_router.post("/heartbeat", response_model=MonitoringAgentResponse, summary="Agent heartbeat")
def agent_heartbeat(
    payload: AgentHeartbeatRequest,
    db: DbSession,
    agent: AgentContext,
) -> MonitoringAgentResponse:
    return MonitoringAgentService(db).record_heartbeat(agent, payload)


@agent_router.post("/metrics", summary="Ingest metrics from agent")
def agent_ingest_metrics(
    payload: AgentMetricsIngestRequest,
    db: DbSession,
    agent: AgentContext,
) -> dict[str, int]:
    return MonitoringAgentService(db).ingest_metrics(agent, payload)


@agent_router.post("/logs", summary="Ingest logs from agent")
def agent_ingest_logs(
    payload: AgentLogsIngestRequest,
    db: DbSession,
    agent: AgentContext,
) -> dict[str, int]:
    return MonitoringAgentService(db).ingest_logs(agent, payload)
