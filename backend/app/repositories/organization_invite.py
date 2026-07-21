from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import InviteStatus
from app.models.organization_invite import OrganizationInvite
from app.repositories.base import BaseRepository


class OrganizationInviteRepository(BaseRepository[OrganizationInvite]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, OrganizationInvite)

    def get_by_token_hash(self, token_hash: str) -> Optional[OrganizationInvite]:
        stmt = select(OrganizationInvite).where(OrganizationInvite.token_hash == token_hash)
        return self.db.scalar(stmt)

    def list_for_organization(
        self, organization_id: int, *, status: Optional[str] = None
    ) -> Sequence[OrganizationInvite]:
        stmt = select(OrganizationInvite).where(
            OrganizationInvite.organization_id == organization_id
        )
        if status:
            stmt = stmt.where(OrganizationInvite.status == status)
        return self.db.scalars(stmt.order_by(OrganizationInvite.created_at.desc())).all()

    def get_pending_for_email(
        self, organization_id: int, email: str
    ) -> Optional[OrganizationInvite]:
        stmt = select(OrganizationInvite).where(
            OrganizationInvite.organization_id == organization_id,
            OrganizationInvite.email == email.lower(),
            OrganizationInvite.status == InviteStatus.PENDING.value,
        )
        return self.db.scalar(stmt)

    def mark_expired_pending(self) -> None:
        now = datetime.now(timezone.utc)
        stmt = select(OrganizationInvite).where(
            OrganizationInvite.status == InviteStatus.PENDING.value,
            OrganizationInvite.expires_at < now,
        )
        for invite in self.db.scalars(stmt).all():
            invite.status = InviteStatus.EXPIRED.value
        self.db.flush()
