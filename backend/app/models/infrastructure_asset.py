from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import AssetStatus, AssetType, EnvironmentType

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.project import Project
    from app.models.user import User


class InfrastructureAsset(Base):
    __tablename__ = "infrastructure_assets"
    __table_args__ = (
        UniqueConstraint("organization_id", "hostname", name="uq_asset_org_hostname"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    environment: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EnvironmentType.PRODUCTION.value
    )
    owner_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AssetStatus.UNKNOWN.value
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="assets", lazy="selectin"
    )
    project: Mapped[Optional["Project"]] = relationship(
        "Project", back_populates="assets", lazy="selectin"
    )
    owner: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    @property
    def tags_list(self) -> list[str]:
        if not self.tags:
            return []
        try:
            data = json.loads(self.tags)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    @tags_list.setter
    def tags_list(self, value: list[str]) -> None:
        self.tags = json.dumps(value)

    @property
    def metadata_dict(self) -> dict[str, Any]:
        if not self.metadata_json:
            return {}
        try:
            data = json.loads(self.metadata_json)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    @metadata_dict.setter
    def metadata_dict(self, value: dict[str, Any]) -> None:
        self.metadata_json = json.dumps(value)
