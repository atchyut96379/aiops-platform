from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from app.api.v1.deps import CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.audit import AuditLogResponse
from app.security.rbac import require_roles
from app.services.audit import AuditService

router = APIRouter(prefix="/organizations/me/audit-logs", tags=["Audit Logs"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("", response_model=list[AuditLogResponse], summary="List audit logs")
def list_audit_logs(
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
    action: Optional[str] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[AuditLogResponse]:
    return AuditService(db).list_logs(
        organization_id=_org_id(current),
        requester=current.user,
        roles=current.roles,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        skip=skip,
        limit=limit,
    )


@router.get("/export", response_class=PlainTextResponse, summary="Export audit logs CSV")
def export_audit_logs(
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> PlainTextResponse:
    csv_data = AuditService(db).export_csv(
        organization_id=_org_id(current),
        requester=current.user,
        roles=current.roles,
    )
    return PlainTextResponse(csv_data, media_type="text/csv")


@router.get("/{log_id}", response_model=AuditLogResponse, summary="Get audit log entry")
def get_audit_log(
    log_id: int,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> AuditLogResponse:
    return AuditService(db).get_log(
        organization_id=_org_id(current),
        log_id=log_id,
        requester=current.user,
        roles=current.roles,
    )
