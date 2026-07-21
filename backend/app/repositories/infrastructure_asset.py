from typing import Any, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.infrastructure_asset import InfrastructureAsset
from app.repositories.base import BaseRepository


class InfrastructureAssetRepository(BaseRepository[InfrastructureAsset]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, InfrastructureAsset)

    def get_by_hostname(self, organization_id: int, hostname: str) -> Optional[InfrastructureAsset]:
        stmt = select(InfrastructureAsset).where(
            InfrastructureAsset.organization_id == organization_id,
            InfrastructureAsset.hostname == hostname,
        )
        return self.db.scalar(stmt)

    def list_for_organization(
        self,
        organization_id: int,
        *,
        asset_type: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        project_id: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[InfrastructureAsset]:
        stmt = select(InfrastructureAsset).where(
            InfrastructureAsset.organization_id == organization_id,
            InfrastructureAsset.is_active.is_(True),
        )
        if asset_type:
            stmt = stmt.where(InfrastructureAsset.asset_type == asset_type)
        if environment:
            stmt = stmt.where(InfrastructureAsset.environment == environment)
        if status:
            stmt = stmt.where(InfrastructureAsset.status == status)
        if project_id is not None:
            stmt = stmt.where(InfrastructureAsset.project_id == project_id)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                InfrastructureAsset.hostname.ilike(pattern)
                | InfrastructureAsset.ip_address.ilike(pattern)
            )
        stmt = stmt.order_by(InfrastructureAsset.hostname).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def count_for_organization(self, organization_id: int) -> int:
        stmt = select(func.count()).select_from(InfrastructureAsset).where(
            InfrastructureAsset.organization_id == organization_id,
            InfrastructureAsset.is_active.is_(True),
        )
        return int(self.db.scalar(stmt) or 0)

    def stats_by_type(self, organization_id: int) -> list[tuple[str, int]]:
        stmt = (
            select(InfrastructureAsset.asset_type, func.count())
            .where(
                InfrastructureAsset.organization_id == organization_id,
                InfrastructureAsset.is_active.is_(True),
            )
            .group_by(InfrastructureAsset.asset_type)
        )
        return list(self.db.execute(stmt).all())

    def stats_by_status(self, organization_id: int) -> list[tuple[str, int]]:
        stmt = (
            select(InfrastructureAsset.status, func.count())
            .where(
                InfrastructureAsset.organization_id == organization_id,
                InfrastructureAsset.is_active.is_(True),
            )
            .group_by(InfrastructureAsset.status)
        )
        return list(self.db.execute(stmt).all())
