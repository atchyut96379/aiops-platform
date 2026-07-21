from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.monitoring_metric import MonitoringMetric
from app.repositories.base import BaseRepository


class MonitoringMetricRepository(BaseRepository[MonitoringMetric]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MonitoringMetric)

    def list_for_asset(
        self,
        organization_id: int,
        asset_id: int,
        metric_type: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[MonitoringMetric]:
        stmt = select(MonitoringMetric).where(
            MonitoringMetric.organization_id == organization_id,
            MonitoringMetric.asset_id == asset_id,
        )
        if metric_type:
            stmt = stmt.where(MonitoringMetric.metric_type == metric_type)
        if start_at is not None:
            stmt = stmt.where(MonitoringMetric.recorded_at >= start_at)
        if end_at is not None:
            stmt = stmt.where(MonitoringMetric.recorded_at <= end_at)
        stmt = stmt.order_by(MonitoringMetric.recorded_at.desc()).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def latest_for_asset(self, organization_id: int, asset_id: int) -> Sequence[MonitoringMetric]:
        stmt = (
            select(MonitoringMetric)
            .where(
                MonitoringMetric.organization_id == organization_id,
                MonitoringMetric.asset_id == asset_id,
            )
            .order_by(MonitoringMetric.recorded_at.desc())
            .limit(100)
        )
        return self.db.scalars(stmt).all()

    def stats_by_asset(self, organization_id: int, asset_id: int) -> list[tuple[str, int]]:
        stmt = (
            select(MonitoringMetric.metric_type, func.count())
            .where(
                MonitoringMetric.organization_id == organization_id,
                MonitoringMetric.asset_id == asset_id,
            )
            .group_by(MonitoringMetric.metric_type)
        )
        return list(self.db.execute(stmt).all())

    def recent_for_organization(
        self,
        organization_id: int,
        metric_type: Optional[str] = None,
        limit: int = 100,
    ) -> Sequence[MonitoringMetric]:
        stmt = select(MonitoringMetric).where(MonitoringMetric.organization_id == organization_id)
        if metric_type is not None:
            stmt = stmt.where(MonitoringMetric.metric_type == metric_type)
        stmt = stmt.order_by(MonitoringMetric.recorded_at.desc()).limit(limit)
        return self.db.scalars(stmt).all()
