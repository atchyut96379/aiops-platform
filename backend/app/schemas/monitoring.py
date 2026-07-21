from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class MonitoringMetricCreate(BaseModel):
    metric_type: str = Field(min_length=1, max_length=100)
    metric_value: Optional[float] = None
    unit: Optional[str] = Field(default=None, max_length=50)
    details: dict[str, Any] = Field(default_factory=dict)
    recorded_at: Optional[datetime] = None


class MonitoringMetricResponse(ORMModel):
    id: int
    organization_id: int
    asset_id: Optional[int] = None
    metric_type: str
    metric_value: Optional[float] = None
    unit: Optional[str] = None
    details: dict[str, Any] = {}
    recorded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MonitoringMetricStats(BaseModel):
    count_by_type: dict[str, int]


class MonitoringHealthSummary(BaseModel):
    asset_id: int
    asset_hostname: str
    status: str
    message: str
    metrics: dict[str, Any] = Field(default_factory=dict)
