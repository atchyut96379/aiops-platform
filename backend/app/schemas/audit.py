from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AuditLogResponse(ORMModel):
    id: int
    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
