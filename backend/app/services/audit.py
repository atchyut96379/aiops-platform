import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import AuditLog, User
from app.repositories.audit import AuditLogRepository
from app.repositories.role import UserRoleRepository
from app.models.enums import RoleName
from app.schemas.audit import AuditLogResponse


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditLogRepository(db)
        self.memberships = UserRoleRepository(db)

    def list_logs(
        self,
        *,
        organization_id: int,
        requester: User,
        roles: list[str],
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AuditLogResponse]:
        self._require_admin(requester, organization_id, roles)
        logs = self.audit.list_for_organization(
            organization_id,
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(log) for log in logs]

    def get_log(
        self, *, organization_id: int, log_id: int, requester: User, roles: list[str]
    ) -> AuditLogResponse:
        self._require_admin(requester, organization_id, roles)
        log = self.audit.get(log_id)
        if log is None or log.organization_id != organization_id:
            raise NotFoundError("Audit log not found")
        return self._to_response(log)

    def export_csv(
        self, *, organization_id: int, requester: User, roles: list[str]
    ) -> str:
        self._require_admin(requester, organization_id, roles)
        logs = self.audit.list_for_organization(organization_id, limit=5000)
        lines = ["id,action,user_id,resource_type,resource_id,created_at"]
        for log in logs:
            lines.append(
                f"{log.id},{log.action},{log.user_id or ''},{log.resource_type or ''},"
                f"{log.resource_id or ''},{log.created_at.isoformat() if log.created_at else ''}"
            )
        return "\n".join(lines)

    def _require_admin(self, user: User, organization_id: int, roles: list[str]) -> None:
        if user.is_superuser or RoleName.SUPER_ADMIN.value in roles:
            return
        if RoleName.ORGANIZATION_ADMIN.value not in roles:
            raise ForbiddenError("Organization admin role required")
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")

    def _to_response(self, log: AuditLog) -> AuditLogResponse:
        details: dict = {}
        if log.details:
            try:
                parsed = json.loads(log.details)
                if isinstance(parsed, dict):
                    details = parsed
            except json.JSONDecodeError:
                details = {"raw": log.details}
        return AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            organization_id=log.organization_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            details=details,
            created_at=log.created_at,
        )
