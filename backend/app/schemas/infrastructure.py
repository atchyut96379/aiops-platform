from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.enums import AssetStatus, AssetType, EnvironmentType
from app.schemas.common import ORMModel


class InfrastructureAssetCreate(BaseModel):
    asset_type: AssetType
    hostname: str = Field(min_length=1, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    os: Optional[str] = Field(default=None, max_length=100)
    environment: EnvironmentType = EnvironmentType.PRODUCTION
    owner_user_id: Optional[int] = None
    project_id: Optional[int] = None
    tags: list[str] = Field(default_factory=list)
    status: AssetStatus = AssetStatus.UNKNOWN
    metadata: dict[str, Any] = Field(default_factory=dict)


class InfrastructureAssetUpdate(BaseModel):
    asset_type: Optional[AssetType] = None
    hostname: Optional[str] = Field(default=None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    os: Optional[str] = Field(default=None, max_length=100)
    environment: Optional[EnvironmentType] = None
    owner_user_id: Optional[int] = None
    project_id: Optional[int] = None
    tags: Optional[list[str]] = None
    status: Optional[AssetStatus] = None
    metadata: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class InfrastructureAssetResponse(ORMModel):
    id: int
    organization_id: int
    project_id: Optional[int] = None
    asset_type: str
    hostname: str
    ip_address: Optional[str] = None
    os: Optional[str] = None
    environment: str
    owner_user_id: Optional[int] = None
    tags: list[str] = []
    status: str
    metadata: dict[str, Any] = {}
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class InfrastructureAssetStats(BaseModel):
    total: int
    by_type: dict[str, int]
    by_status: dict[str, int]
