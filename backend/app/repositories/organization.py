from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Organization)

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.slug == slug)
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.name == name)
        return self.db.scalar(stmt)

    def list_for_user(self, user_id: int) -> Sequence[Organization]:
        from app.models.user_role import UserRole

        stmt = (
            select(Organization)
            .join(UserRole, UserRole.organization_id == Organization.id)
            .where(UserRole.user_id == user_id, Organization.is_active.is_(True))
            .distinct()
            .order_by(Organization.name)
        )
        return self.db.scalars(stmt).all()

    def list_all(self) -> Sequence[Organization]:
        stmt = select(Organization).where(Organization.is_active.is_(True)).order_by(Organization.name)
        return self.db.scalars(stmt).all()
