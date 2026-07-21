from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import AlertLevel, NotificationChannelType

if TYPE_CHECKING:
    from app.models.organization import Organization


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    min_alert_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AlertLevel.MEDIUM.value
    )
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
        "Organization", back_populates="notification_channels", lazy="selectin"
    )
    logs: Mapped[list["NotificationLog"]] = relationship(
        "NotificationLog", back_populates="channel", lazy="selectin"
    )

    @property
    def config(self) -> dict[str, Any]:
        try:
            data = json.loads(self.config_json or "{}")
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    @config.setter
    def config(self, value: dict[str, Any]) -> None:
        self.config_json = json.dumps(value)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("notification_channels.id", ondelete="SET NULL"), nullable=True, index=True
    )
    alert_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    channel: Mapped[Optional["NotificationChannel"]] = relationship(
        "NotificationChannel", back_populates="logs", lazy="selectin"
    )
