from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class LogEntryCreate(BaseModel):
    level: str = Field(default="info", max_length=20)
    message: str = Field(min_length=1, max_length=10000)
    source: str = Field(default="api", max_length=100)
    host: Optional[str] = Field(default=None, max_length=255)
    asset_id: Optional[int] = None
    logged_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LogBatchCreate(BaseModel):
    logs: list[LogEntryCreate] = Field(min_length=1, max_length=500)


class LogEntryResponse(ORMModel):
    id: int
    organization_id: int
    asset_id: Optional[int] = None
    source: str
    level: str
    message: str
    host: Optional[str] = None
    logged_at: datetime
    metadata: dict[str, Any] = {}
    created_at: Optional[datetime] = None


class LogSearchResponse(BaseModel):
    items: list[LogEntryResponse]
    total: int
