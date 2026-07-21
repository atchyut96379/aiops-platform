from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Project)

    def get_by_slug(self, organization_id: int, slug: str) -> Optional[Project]:
        stmt = select(Project).where(
            Project.organization_id == organization_id,
            Project.slug == slug,
        )
        return self.db.scalar(stmt)

    def list_for_organization(
        self,
        organization_id: int,
        *,
        team_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Project]:
        stmt = select(Project).where(Project.organization_id == organization_id)
        if team_id is not None:
            stmt = stmt.where(Project.team_id == team_id)
        stmt = stmt.order_by(Project.name).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()
