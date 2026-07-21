from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import CurrentUser, DbSession, get_client_meta
from app.models.enums import RoleName
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate
from app.security.rbac import require_any_authenticated, require_roles
from app.services.incident import IncidentService

router = APIRouter(prefix="/organizations/me/incidents", tags=["Incidents"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an incident",
)
def create_incident(
    payload: IncidentCreate,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> IncidentResponse:
    return IncidentService(db).create_incident(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
    )


@router.get("", response_model=list[IncidentResponse], summary="List incidents")
def list_incidents(
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
    asset_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[IncidentResponse]:
    return IncidentService(db).list_incidents(
        organization_id=_org_id(current),
        requester=current.user,
        asset_id=asset_id,
        status=status,
        severity=severity,
        skip=skip,
        limit=limit,
    )


@router.get("/{incident_id}", response_model=IncidentResponse, summary="Get incident details")
def get_incident(
    incident_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> IncidentResponse:
    return IncidentService(db).get_incident(
        organization_id=_org_id(current),
        incident_id=incident_id,
        requester=current.user,
    )


@router.patch("/{incident_id}", response_model=IncidentResponse, summary="Update an incident")
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.SUPPORT_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> IncidentResponse:
    return IncidentService(db).update_incident(
        organization_id=_org_id(current),
        incident_id=incident_id,
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )
