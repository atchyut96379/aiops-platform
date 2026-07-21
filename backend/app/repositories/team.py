from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.team import Team, TeamMember
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Team)

    def get_by_slug(self, organization_id: int, slug: str) -> Optional[Team]:
        stmt = select(Team).where(
            Team.organization_id == organization_id,
            Team.slug == slug,
        )
        return self.db.scalar(stmt)

    def list_for_organization(
        self, organization_id: int, *, skip: int = 0, limit: int = 50
    ) -> Sequence[Team]:
        stmt = (
            select(Team)
            .where(Team.organization_id == organization_id)
            .order_by(Team.name)
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(stmt).all()


class TeamMemberRepository(BaseRepository[TeamMember]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TeamMember)

    def get_membership(self, team_id: int, user_id: int) -> Optional[TeamMember]:
        stmt = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def list_for_team(self, team_id: int) -> Sequence[TeamMember]:
        stmt = select(TeamMember).where(TeamMember.team_id == team_id)
        return self.db.scalars(stmt).all()
