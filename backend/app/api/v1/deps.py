from dataclasses import dataclass, field
from typing import Annotated, Optional

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.db.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository

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

    org_id = x_organization_id if x_organization_id is not None else payload.get("org_id")
    roles = list(payload.get("roles") or [])
    is_superuser = bool(payload.get("is_superuser") or user.is_superuser)

    return CurrentUser(
        user=user,
        organization_id=org_id,
        roles=roles,
        is_superuser=is_superuser,
    )


DbSession = Annotated[Session, Depends(get_db)]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
