from dataclasses import dataclass, field
from typing import Annotated, Optional

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token, hash_opaque_token
from app.db.database import get_db
from app.models.monitoring_agent import MonitoringAgent
from app.models.user import User
from app.repositories.monitoring_agent import MonitoringAgentRepository
from app.repositories.user import UserRepository
from app.repositories.role import UserRoleRepository
from app.core.exceptions import ForbiddenError

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    user: User
    organization_id: Optional[int] = None
    roles: list[str] = field(default_factory=list)
    is_superuser: bool = False

    @property
    def id(self) -> int:
        return self.user.id


def get_client_meta(request: Request) -> tuple[Optional[str], Optional[str]]:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)
    user_agent = request.headers.get("user-agent")
    return ip, user_agent


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    x_organization_id: Annotated[Optional[int], Header(alias="X-Organization-Id")] = None,
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Not authenticated", code="not_authenticated")

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise UnauthorizedError("Invalid or expired token", code="invalid_token") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid access token", code="invalid_token")

    subject = payload.get("sub")
    if subject is None:
        raise UnauthorizedError("Invalid access token", code="invalid_token")

    user = UserRepository(db).get(int(subject))
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive", code="invalid_token")

    # Determine organization context. Prefer token org unless X-Organization-Id is provided
    # and the user is authorized for that organization. Do NOT allow arbitrary override.
    token_org = payload.get("org_id")
    is_superuser = bool(payload.get("is_superuser") or user.is_superuser)

    if x_organization_id is not None:
        # If user is superuser, allow overriding org context.
        if is_superuser:
            org_id = x_organization_id
        else:
            # Validate membership for requested org
            memberships = UserRoleRepository(db).list_for_user_org(user.id, int(x_organization_id))
            if not memberships:
                raise ForbiddenError("Organization context not allowed", code="forbidden_org")
            org_id = int(x_organization_id)
    else:
        org_id = token_org

    # Compute roles for the resolved organization to avoid stale/forged token roles
    if is_superuser:
        roles = ["SUPER_ADMIN"]
    else:
        if org_id is None:
            roles = []
        else:
            memberships = UserRoleRepository(db).list_for_user_org(user.id, int(org_id))
            roles = [m.role.name for m in memberships if m.role is not None]

    return CurrentUser(
        user=user,
        organization_id=org_id,
        roles=roles,
        is_superuser=is_superuser,
    )


def get_monitoring_agent(
    db: Annotated[Session, Depends(get_db)],
    x_agent_key: Annotated[Optional[str], Header(alias="X-Agent-Key")] = None,
) -> MonitoringAgent:
    if not x_agent_key or not x_agent_key.startswith("aiops_"):
        raise UnauthorizedError("Invalid or missing agent API key", code="invalid_agent_key")

    agent = MonitoringAgentRepository(db).get_by_api_key_hash(hash_opaque_token(x_agent_key))
    if agent is None:
        raise UnauthorizedError("Invalid or inactive agent key", code="invalid_agent_key")
    return agent


DbSession = Annotated[Session, Depends(get_db)]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
AgentContext = Annotated[MonitoringAgent, Depends(get_monitoring_agent)]
