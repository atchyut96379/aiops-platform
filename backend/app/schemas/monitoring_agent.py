from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class MonitoringAgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    asset_id: Optional[int] = None
    hostname: Optional[str] = Field(default=None, max_length=255)


class MonitoringAgentResponse(ORMModel):
    id: int
    organization_id: int
    asset_id: Optional[int] = None
    name: str
    hostname: Optional[str] = None
    api_key_prefix: str
    is_active: bool
    last_heartbeat_at: Optional[datetime] = None
    agent_version: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MonitoringAgentCreatedResponse(MonitoringAgentResponse):
    api_key: str


class AgentHeartbeatRequest(BaseModel):
    agent_version: Optional[str] = Field(default=None, max_length=50)
    hostname: Optional[str] = Field(default=None, max_length=255)


class AgentMetricBatch(BaseModel):
    metric_type: str = Field(min_length=1, max_length=100)
    metric_value: Optional[float] = None
    unit: Optional[str] = Field(default=None, max_length=50)
    recorded_at: Optional[datetime] = None


class AgentMetricsIngestRequest(BaseModel):
    metrics: list[AgentMetricBatch] = Field(min_length=1, max_length=100)


class AgentLogBatch(BaseModel):
    level: str = Field(default="info", max_length=20)
    message: str = Field(min_length=1, max_length=10000)
    source: str = Field(default="agent", max_length=100)
    host: Optional[str] = Field(default=None, max_length=255)
    logged_at: Optional[datetime] = None


class AgentLogsIngestRequest(BaseModel):
    logs: list[AgentLogBatch] = Field(min_length=1, max_length=500)
