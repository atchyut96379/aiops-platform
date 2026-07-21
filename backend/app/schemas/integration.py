from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CloudIntegrationCreate(BaseModel):
    provider: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    credentials: dict[str, Any] = Field(default_factory=dict)


class CloudIntegrationResponse(ORMModel):
    id: int
    organization_id: int
    provider: str
    name: str
    is_active: bool
    last_sync_at: Optional[datetime] = None
    sync_status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CloudSyncResult(BaseModel):
    integration_id: int
    provider: str
    assets_discovered: int
    assets: list[dict[str, Any]]
    message: str
