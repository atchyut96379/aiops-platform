from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.monitoring_agent import MonitoringAgent
from app.repositories.base import BaseRepository


class MonitoringAgentRepository(BaseRepository[MonitoringAgent]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MonitoringAgent)

    def get_by_api_key_hash(self, api_key_hash: str) -> Optional[MonitoringAgent]:
        stmt = select(MonitoringAgent).where(
            MonitoringAgent.api_key_hash == api_key_hash,
            MonitoringAgent.is_active.is_(True),
        )
        return self.db.scalar(stmt)

    def list_for_organization(
        self, organization_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[MonitoringAgent]:
        stmt = (
            select(MonitoringAgent)
            .where(MonitoringAgent.organization_id == organization_id)
            .order_by(MonitoringAgent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def count_for_organization(self, organization_id: int) -> int:
        stmt = select(MonitoringAgent).where(MonitoringAgent.organization_id == organization_id)
        return len(self.db.scalars(stmt).all())
