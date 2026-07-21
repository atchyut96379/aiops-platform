from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PlatformConnectionCreate(BaseModel):
    connection_type: str = Field(pattern="^(docker|kubernetes)$")
    name: str = Field(min_length=1, max_length=200)
    endpoint: Optional[str] = Field(default=None, max_length=500)
    config: dict[str, Any] = Field(default_factory=dict)


class PlatformConnectionResponse(ORMModel):
    id: int
    organization_id: int
    connection_type: str
    name: str
    endpoint: Optional[str] = None
    is_active: bool
    last_collect_at: Optional[datetime] = None
    collect_status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PlatformCollectResult(BaseModel):
    connection_id: int
    connection_type: str
    snapshot: dict[str, Any]
    message: str
