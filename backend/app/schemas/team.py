from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import EnvironmentType
from app.schemas.common import ORMModel


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TeamMemberAdd(BaseModel):
    user_id: int


class TeamResponse(ORMModel):
    id: int
    organization_id: int
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    member_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TeamMemberResponse(ORMModel):
    id: int
    team_id: int
    user_id: int
    user_email: str
    user_name: str
    created_at: Optional[datetime] = None
