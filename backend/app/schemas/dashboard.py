from typing import Any

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_assets: int = 0
    healthy_assets: int = 0
    open_alerts: int = 0
    critical_alerts: int = 0
    open_incidents: int = 0
    closed_incidents: int = 0
    alerts_by_level: dict[str, int] = Field(default_factory=dict)
    incidents_by_severity: dict[str, int] = Field(default_factory=dict)
    assets_by_status: dict[str, int] = Field(default_factory=dict)


class DashboardTrends(BaseModel):
    days: int
    alerts_by_day: dict[str, int] = Field(default_factory=dict)
    incidents_by_day: dict[str, int] = Field(default_factory=dict)
    metrics_by_day: dict[str, int] = Field(default_factory=dict)
