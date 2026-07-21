from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Incident)

    def list_for_organization(
        self,
        organization_id: int,
        asset_id: Optional[int] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Incident]:
        stmt = select(Incident).where(Incident.organization_id == organization_id)
        if asset_id is not None:
            stmt = stmt.where(Incident.asset_id == asset_id)
        if status is not None:
            stmt = stmt.where(Incident.status == status)
        if severity is not None:
            stmt = stmt.where(Incident.severity == severity)
        stmt = stmt.order_by(Incident.created_at.desc()).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()
