from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Alert)

    def list_for_organization(
        self,
        organization_id: int,
        asset_id: Optional[int] = None,
        status: Optional[str] = None,
        level: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Alert]:
        stmt = select(Alert).where(Alert.organization_id == organization_id)
        if asset_id is not None:
            stmt = stmt.where(Alert.asset_id == asset_id)
        if status is not None:
            stmt = stmt.where(Alert.status == status)
        if level is not None:
            stmt = stmt.where(Alert.level == level)
        stmt = stmt.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def mark_acknowledged(self, alert: Alert, by_user_id: int) -> Alert:
        alert.acknowledged = True
        from datetime import datetime

        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by_id = by_user_id
        self.db.flush()
        self.db.refresh(alert)
        return alert

    def mark_resolved(self, alert: Alert, by_user_id: int) -> Alert:
        alert.resolved = True
        from datetime import datetime

        alert.resolved_at = datetime.utcnow()
        alert.resolved_by_id = by_user_id
        alert.status = "resolved"
        self.db.flush()
        self.db.refresh(alert)
        return alert
