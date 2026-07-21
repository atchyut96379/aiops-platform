from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    metric_type: str = Field(min_length=1, max_length=100)
    operator: str = Field(default="gte", pattern="^(gte|lte|gt|lt|eq)$")
    threshold: float
    level: str = Field(min_length=1, max_length=20)
    asset_id: Optional[int] = None
    enabled: bool = True
    cooldown_minutes: int = Field(default=15, ge=1, le=1440)
    description: Optional[str] = None


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    metric_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    operator: Optional[str] = Field(default=None, pattern="^(gte|lte|gt|lt|eq)$")
    threshold: Optional[float] = None
    level: Optional[str] = Field(default=None, min_length=1, max_length=20)
    asset_id: Optional[int] = None
    enabled: Optional[bool] = None
    cooldown_minutes: Optional[int] = Field(default=None, ge=1, le=1440)
    description: Optional[str] = None


class AlertRuleResponse(ORMModel):
    id: int
    organization_id: int
    asset_id: Optional[int] = None
    name: str
    metric_type: str
    operator: str
    threshold: float
    level: str
    enabled: bool
    cooldown_minutes: int
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
