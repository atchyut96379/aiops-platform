from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.infrastructure_asset import InfrastructureAsset
    from app.models.organization import Organization


class MonitoringMetric(Base):
    __tablename__ = "monitoring_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("infrastructure_assets.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    metric_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=func.now(),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship("Organization", lazy="selectin")
    asset: Mapped[Optional["InfrastructureAsset"]] = relationship(
        "InfrastructureAsset", lazy="selectin"
    )

    @property
    def details(self) -> dict[str, Any]:
        if not self.details_json:
            return {}
        try:
            data = json.loads(self.details_json)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    @details.setter
    def details(self, value: dict[str, Any]) -> None:
        self.details_json = json.dumps(value)
