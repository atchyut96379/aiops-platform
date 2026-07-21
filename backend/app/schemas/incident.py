from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.enums import IncidentSeverity, IncidentStatus
from app.schemas.common import ORMModel


class IncidentCreate(BaseModel):
    asset_id: Optional[int] = None
    incident_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    details: dict[str, Any] = Field(default_factory=dict)


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assignee_user_id: Optional[int] = None
    resolution: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class IncidentResponse(ORMModel):
    id: int
    organization_id: int
    asset_id: Optional[int] = None
    incident_type: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    assignee_user_id: Optional[int] = None
    resolution: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)
    comment_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IncidentCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class IncidentCommentResponse(ORMModel):
    id: int
    incident_id: int
    user_id: int
    author_name: str
    author_email: str
    body: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
