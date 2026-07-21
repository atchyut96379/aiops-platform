from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AlertCreate(BaseModel):
    asset_id: Optional[int] = None
    alert_type: str = Field(min_length=1, max_length=100)
    level: str = Field(min_length=1, max_length=20)
    details: dict[str, Any] = Field(default_factory=dict)


class AlertResponse(ORMModel):
    id: int
    organization_id: int
    asset_id: Optional[int] = None
    alert_type: str
    level: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_id: Optional[int] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
