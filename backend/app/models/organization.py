from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import SubscriptionPlan

if TYPE_CHECKING:
    from app.models.user_role import UserRole


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    subscription_plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SubscriptionPlan.FREE.value,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    memberships: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
