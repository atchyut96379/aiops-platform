from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.v1.deps import CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.incident import (
    IncidentAttachmentResponse,
    IncidentCommentCreate,
    IncidentCommentResponse,
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)
from app.security.rbac import require_any_authenticated, require_roles
from app.services.attachment import AttachmentService
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


@router.get(
    "/{incident_id}/comments",
    response_model=list[IncidentCommentResponse],
    summary="List incident comments",
)
def list_incident_comments(
    incident_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> list[IncidentCommentResponse]:
    return IncidentService(db).list_comments(
        organization_id=_org_id(current),
        incident_id=incident_id,
        requester=current.user,
    )


@router.post(
    "/{incident_id}/comments",
    response_model=IncidentCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add incident comment",
)
def add_incident_comment(
    incident_id: int,
    payload: IncidentCommentCreate,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> IncidentCommentResponse:
    return IncidentService(db).add_comment(
        organization_id=_org_id(current),
        incident_id=incident_id,
        payload=payload,
        requester=current.user,
    )


@router.get(
    "/{incident_id}/attachments",
    response_model=list[IncidentAttachmentResponse],
    summary="List incident attachments",
)
def list_incident_attachments(
    incident_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> list[IncidentAttachmentResponse]:
    return AttachmentService(db).list_attachments(
        organization_id=_org_id(current),
        incident_id=incident_id,
        requester=current.user,
    )


@router.post(
    "/{incident_id}/attachments",
    response_model=IncidentAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload incident attachment",
)
async def upload_incident_attachment(
    incident_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
    file: UploadFile = File(...),
) -> IncidentAttachmentResponse:
    return await AttachmentService(db).upload(
        organization_id=_org_id(current),
        incident_id=incident_id,
        requester=current.user,
        file=file,
    )


@router.get(
    "/{incident_id}/attachments/{attachment_id}/download",
    summary="Download incident attachment",
)
def download_incident_attachment(
    incident_id: int,
    attachment_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
) -> FileResponse:
    attachment, path = AttachmentService(db).get_path(
        organization_id=_org_id(current),
        incident_id=incident_id,
        attachment_id=attachment_id,
        requester=current.user,
    )
    return FileResponse(
        path,
        filename=attachment.filename,
        media_type=attachment.content_type or "application/octet-stream",
    )


@router.delete(
    "/{incident_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete incident attachment",
)
def delete_incident_attachment(
    incident_id: int,
    attachment_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.SUPPORT_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> None:
    AttachmentService(db).delete(
        organization_id=_org_id(current),
        incident_id=incident_id,
        attachment_id=attachment_id,
        requester=current.user,
    )
