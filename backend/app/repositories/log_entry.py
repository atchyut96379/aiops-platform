from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.log_entry import LogEntry
from app.repositories.base import BaseRepository


class LogEntryRepository(BaseRepository[LogEntry]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, LogEntry)

    def search(
        self,
        organization_id: int,
        *,
        query: Optional[str] = None,
        level: Optional[str] = None,
        asset_id: Optional[int] = None,
        source: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[LogEntry]:
        stmt = select(LogEntry).where(LogEntry.organization_id == organization_id)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(LogEntry.message.ilike(pattern), LogEntry.host.ilike(pattern))
            )
        if level:
            stmt = stmt.where(LogEntry.level == level)
        if asset_id is not None:
            stmt = stmt.where(LogEntry.asset_id == asset_id)
        if source:
            stmt = stmt.where(LogEntry.source == source)
        if start_at:
            stmt = stmt.where(LogEntry.logged_at >= start_at)
        if end_at:
            stmt = stmt.where(LogEntry.logged_at <= end_at)
        stmt = stmt.order_by(LogEntry.logged_at.desc()).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def count_for_organization(self, organization_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(LogEntry)
                .where(LogEntry.organization_id == organization_id)
            )
            or 0
        )

    def add_batch(self, entries: list[LogEntry]) -> None:
        self.db.add_all(entries)
        self.db.flush()
