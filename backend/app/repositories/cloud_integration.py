from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cloud_integration import CloudIntegration
from app.repositories.base import BaseRepository


class CloudIntegrationRepository(BaseRepository[CloudIntegration]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CloudIntegration)

    def list_for_organization(
        self, organization_id: int, provider: Optional[str] = None
    ) -> Sequence[CloudIntegration]:
        stmt = select(CloudIntegration).where(CloudIntegration.organization_id == organization_id)
        if provider:
            stmt = stmt.where(CloudIntegration.provider == provider)
        return self.db.scalars(stmt.order_by(CloudIntegration.created_at.desc())).all()

    def count_for_organization(self, organization_id: int) -> int:
        stmt = select(CloudIntegration).where(CloudIntegration.organization_id == organization_id)
        return len(self.db.scalars(stmt).all())
