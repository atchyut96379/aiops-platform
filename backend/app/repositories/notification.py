from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import NotificationChannel, NotificationLog
from app.repositories.base import BaseRepository


class NotificationChannelRepository(BaseRepository[NotificationChannel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, NotificationChannel)

    def list_for_organization(
        self, organization_id: int, *, active_only: bool = True
    ) -> Sequence[NotificationChannel]:
        stmt = select(NotificationChannel).where(
            NotificationChannel.organization_id == organization_id
        )
        if active_only:
            stmt = stmt.where(NotificationChannel.is_active.is_(True))
        return self.db.scalars(stmt.order_by(NotificationChannel.name)).all()


class NotificationLogRepository(BaseRepository[NotificationLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, NotificationLog)

    def list_for_organization(
        self, organization_id: int, *, skip: int = 0, limit: int = 50
    ) -> Sequence[NotificationLog]:
        stmt = (
            select(NotificationLog)
            .where(NotificationLog.organization_id == organization_id)
            .order_by(NotificationLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(stmt).all()
