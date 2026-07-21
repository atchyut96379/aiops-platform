from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.log_entry import LogBatchCreate, LogSearchResponse
from app.security.rbac import require_any_authenticated, require_roles
from app.services.log_collection import LogCollectionService

router = APIRouter(prefix="/organizations/me/logs", tags=["Logs"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("", response_model=LogSearchResponse, summary="Search centralized logs")
def search_logs(
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
    q: Optional[str] = Query(default=None, max_length=500),
    level: Optional[str] = Query(default=None, max_length=20),
    asset_id: Optional[int] = Query(default=None),
    source: Optional[str] = Query(default=None, max_length=100),
    start_at: Optional[datetime] = Query(default=None),
    end_at: Optional[datetime] = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> LogSearchResponse:
    return LogCollectionService(db).search_logs(
        organization_id=_org_id(current),
        requester=current.user,
        query=q,
        level=level,
        asset_id=asset_id,
        source=source,
        start_at=start_at,
        end_at=end_at,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest log batch",
)
def ingest_logs(
    payload: LogBatchCreate,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.DEVOPS_ENGINEER,
        RoleName.CLOUD_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> dict[str, int]:
    return LogCollectionService(db).ingest_batch(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )
