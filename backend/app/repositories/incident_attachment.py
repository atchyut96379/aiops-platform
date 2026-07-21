from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident_attachment import IncidentAttachment
from app.repositories.base import BaseRepository


class IncidentAttachmentRepository(BaseRepository[IncidentAttachment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, IncidentAttachment)

    def list_for_incident(self, incident_id: int) -> Sequence[IncidentAttachment]:
        stmt = select(IncidentAttachment).where(IncidentAttachment.incident_id == incident_id)
        return self.db.scalars(stmt.order_by(IncidentAttachment.created_at.desc())).all()
