from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.infrastructure_asset import InfrastructureAsset
    from app.models.user import User
    from app.models.organization import Organization


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("infrastructure_assets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    assignee_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization", lazy="selectin")
    asset: Mapped[Optional["InfrastructureAsset"]] = relationship(
        "InfrastructureAsset", lazy="selectin"
    )
    assignee: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    @property
    def details(self) -> dict[str, Any]:
        if not self.details_json:
            return {}
        try:
            parsed = json.loads(self.details_json)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    @details.setter
    def details(self, value: dict[str, Any]) -> None:
        self.details_json = json.dumps(value)
