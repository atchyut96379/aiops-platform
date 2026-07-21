from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident_comment import IncidentComment
from app.repositories.base import BaseRepository


class IncidentCommentRepository(BaseRepository[IncidentComment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, IncidentComment)

    def list_for_incident(self, incident_id: int) -> Sequence[IncidentComment]:
        stmt = (
            select(IncidentComment)
            .where(IncidentComment.incident_id == incident_id)
            .order_by(IncidentComment.created_at.asc())
        )
        return self.db.scalars(stmt).all()
