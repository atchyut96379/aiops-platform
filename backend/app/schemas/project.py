from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import EnvironmentType
from app.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: Optional[str] = None
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    team_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = None
    environment: Optional[EnvironmentType] = None
    team_id: Optional[int] = None
    is_active: Optional[bool] = None


class ProjectResponse(ORMModel):
    id: int
    organization_id: int
    team_id: Optional[int] = None
    name: str
    slug: str
    description: Optional[str] = None
    environment: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
