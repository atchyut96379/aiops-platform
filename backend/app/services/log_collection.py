from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.log_entry import LogEntry
from app.models.enums import RoleName
from app.models.user import User
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.log_entry import LogEntryRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.role import UserRoleRepository
from app.schemas.log_entry import (
    LogBatchCreate,
    LogEntryCreate,
    LogEntryResponse,
    LogSearchResponse,
)
from app.schemas.monitoring_agent import AgentLogsIngestRequest
from app.services.subscription import get_plan_limits


class LogCollectionService:
    WRITE_ROLES = {
        RoleName.ORGANIZATION_ADMIN.value,
        RoleName.DEVOPS_ENGINEER.value,
        RoleName.CLOUD_ENGINEER.value,
        RoleName.SUPER_ADMIN.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.logs = LogEntryRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.orgs = OrganizationRepository(db)
        self.memberships = UserRoleRepository(db)

    def ingest_batch(
        self,
        *,
        organization_id: int,
        payload: LogBatchCreate,
        requester: User,
        roles: list[str],
    ) -> dict[str, int]:
        self._require_write_access(requester, organization_id, roles)
        self._enforce_log_limits(organization_id, len(payload.logs))
        entries = [
            self._build_entry(organization_id, item) for item in payload.logs
        ]
        self.logs.add_batch(entries)
        self.db.commit()
        return {"ingested": len(entries)}

    def ingest_from_agent(
        self,
        *,
        organization_id: int,
        asset_id: Optional[int],
        payload: AgentLogsIngestRequest,
    ) -> dict[str, int]:
        self._enforce_log_limits(organization_id, len(payload.logs))
        entries = []
        for item in payload.logs:
            entry = LogEntry(
                organization_id=organization_id,
                asset_id=asset_id,
                source=item.source,
                level=item.level,
                message=item.message,
                host=item.host,
                logged_at=item.logged_at or datetime.now(timezone.utc),
            )
            entries.append(entry)
        self.logs.add_batch(entries)
        self.db.commit()
        return {"ingested": len(entries)}

    def search_logs(
        self,
        *,
        organization_id: int,
        requester: User,
        query: Optional[str] = None,
        level: Optional[str] = None,
        asset_id: Optional[int] = None,
        source: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> LogSearchResponse:
        self._require_member(requester, organization_id)
        entries = self.logs.search(
            organization_id,
            query=query,
            level=level,
            asset_id=asset_id,
            source=source,
            start_at=start_at,
            end_at=end_at,
            skip=skip,
            limit=limit,
        )
        total = self.logs.count_for_organization(organization_id)
        return LogSearchResponse(
            items=[self._to_response(entry) for entry in entries],
            total=total,
        )

    def _build_entry(self, organization_id: int, item: LogEntryCreate) -> LogEntry:
        if item.asset_id is not None:
            asset = self.assets.get(item.asset_id)
            if asset is None or asset.organization_id != organization_id:
                raise NotFoundError("Asset not found")
        entry = LogEntry(
            organization_id=organization_id,
            asset_id=item.asset_id,
            source=item.source,
            level=item.level,
            message=item.message,
            host=item.host,
            logged_at=item.logged_at or datetime.now(timezone.utc),
        )
        entry.log_metadata = item.metadata
        return entry

    def _enforce_log_limits(self, organization_id: int, incoming: int) -> None:
        org = self.orgs.get(organization_id)
        if org is None:
            raise NotFoundError("Organization not found")
        limits = get_plan_limits(org.subscription_plan)
        current = self.logs.count_for_organization(organization_id)
        if current + incoming > limits.max_log_entries:
            raise ValidationAppError(
                f"Log storage limit reached for {org.subscription_plan} plan"
            )

    def _to_response(self, entry: LogEntry) -> LogEntryResponse:
        return LogEntryResponse(
            id=entry.id,
            organization_id=entry.organization_id,
            asset_id=entry.asset_id,
            source=entry.source,
            level=entry.level,
            message=entry.message,
            host=entry.host,
            logged_at=entry.logged_at,
            metadata=entry.log_metadata,
            created_at=entry.created_at,
        )

    def _require_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")

    def _require_write_access(self, user: User, organization_id: int, roles: list[str]) -> None:
        self._require_member(user, organization_id)
        if user.is_superuser or RoleName.SUPER_ADMIN.value in roles:
            return
        if not self.WRITE_ROLES.intersection(roles):
            raise ForbiddenError("Insufficient permissions to ingest logs")
