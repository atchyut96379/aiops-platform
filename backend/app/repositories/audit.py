import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.user import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AuditLog)

    def record(
        self,
        *,
        action: str,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str | dict[str, Any]] = None,
    ) -> AuditLog:
        details_value: Optional[str]
        if isinstance(details, dict):
            details_value = json.dumps(details)
        else:
            details_value = details

        entry = AuditLog(
            action=action,
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details_value,
        )
        return self.add(entry)
