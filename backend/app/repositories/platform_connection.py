from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.platform_connection import PlatformConnection
from app.repositories.base import BaseRepository


class PlatformConnectionRepository(BaseRepository[PlatformConnection]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PlatformConnection)

    def list_for_organization(
        self, organization_id: int, connection_type: Optional[str] = None
    ) -> Sequence[PlatformConnection]:
        stmt = select(PlatformConnection).where(PlatformConnection.organization_id == organization_id)
        if connection_type:
            stmt = stmt.where(PlatformConnection.connection_type == connection_type)
        return self.db.scalars(stmt.order_by(PlatformConnection.created_at.desc())).all()
