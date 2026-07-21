from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import RoleName
from app.schemas.common import ORMModel
from app.schemas.user import UserResponse


class OrganizationMemberResponse(BaseModel):
    user: UserResponse
    roles: list[str] = []


class MemberRolesUpdate(BaseModel):
    roles: list[RoleName] = Field(min_length=1)


class OrganizationInviteCreate(BaseModel):
    email: EmailStr
    role: RoleName = RoleName.READ_ONLY


class OrganizationInviteResponse(ORMModel):
    id: int
    organization_id: int
    email: EmailStr
    role_name: str
    status: str
    invited_by_user_id: int
    expires_at: datetime
    created_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None


class SwitchOrganizationRequest(BaseModel):
    organization_id: int
