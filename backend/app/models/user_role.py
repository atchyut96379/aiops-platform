from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.role import Role
    from app.models.user import User


class UserRole(Base):
    """Membership of a user in an organization with a role (multi-tenant RBAC)."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", "role_id", name="uq_user_org_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="memberships", lazy="selectin")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="memberships", lazy="selectin"
    )
    role: Mapped["Role"] = relationship("Role", back_populates="memberships", lazy="selectin")
