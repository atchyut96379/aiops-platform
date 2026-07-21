from typing import Optional

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
