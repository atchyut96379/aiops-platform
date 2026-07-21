from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import SubscriptionPlan
from app.schemas.common import ORMModel


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    subscription_plan: Optional[SubscriptionPlan] = None


class OrganizationResponse(ORMModel):
    id: int
    name: str
    slug: str
    logo_url: Optional[str] = None
    subscription_plan: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
