from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert_rule import AlertRule
from app.repositories.base import BaseRepository


class AlertRuleRepository(BaseRepository[AlertRule]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AlertRule)

    def list_for_organization(
        self,
        organization_id: int,
        asset_id: Optional[int] = None,
        enabled_only: bool = False,
        skip: int = 0,
        limit: int = 200,
    ) -> Sequence[AlertRule]:
        stmt = select(AlertRule).where(AlertRule.organization_id == organization_id)
        if asset_id is not None:
            stmt = stmt.where(AlertRule.asset_id == asset_id)
        if enabled_only:
            stmt = stmt.where(AlertRule.enabled.is_(True))
        stmt = stmt.order_by(AlertRule.created_at.desc()).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def count_for_organization(self, organization_id: int) -> int:
        stmt = select(AlertRule).where(AlertRule.organization_id == organization_id)
        return len(self.db.scalars(stmt).all())

    def get_matching_rules(
        self,
        organization_id: int,
        metric_type: str,
        asset_id: Optional[int],
    ) -> Sequence[AlertRule]:
        stmt = select(AlertRule).where(
            AlertRule.organization_id == organization_id,
            AlertRule.metric_type == metric_type,
            AlertRule.enabled.is_(True),
        )
        if asset_id is not None:
            stmt = stmt.where(
                (AlertRule.asset_id == asset_id) | (AlertRule.asset_id.is_(None))
            )
        else:
            stmt = stmt.where(AlertRule.asset_id.is_(None))
        return self.db.scalars(stmt).all()

    def get_recent_alert_for_rule(
        self,
        organization_id: int,
        rule_id: int,
        asset_id: Optional[int],
        since: datetime,
    ) -> bool:
        from app.models.alert import Alert

        stmt = select(Alert).where(
            Alert.organization_id == organization_id,
            Alert.created_at >= since,
        )
        if asset_id is not None:
            stmt = stmt.where(Alert.asset_id == asset_id)
        alerts = self.db.scalars(stmt).all()
        for alert in alerts:
            details = alert.details or {}
            if details.get("rule_id") == rule_id:
                return True
        return False
