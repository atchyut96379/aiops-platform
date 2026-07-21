from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.organization import Organization


class PlatformConnection(Base):
    """Docker host or Kubernetes cluster connection for container platform monitoring."""

    __tablename__ = "platform_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    connection_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("infrastructure_assets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    endpoint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    last_collect_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    collect_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="idle", default="idle")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization", lazy="selectin")

    @property
    def config(self) -> dict:
        if not self.config_json:
            return {}
        try:
            parsed = json.loads(self.config_json)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    @config.setter
    def config(self, value: dict) -> None:
        self.config_json = json.dumps(value)
