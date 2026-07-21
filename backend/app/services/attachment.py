import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.incident_attachment import IncidentAttachment
from app.models.user import User
from app.repositories.incident import IncidentRepository
from app.repositories.incident_attachment import IncidentAttachmentRepository
from app.repositories.role import UserRoleRepository
from app.schemas.incident import IncidentAttachmentResponse


class AttachmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.incidents = IncidentRepository(db)
        self.attachments = IncidentAttachmentRepository(db)
        self.memberships = UserRoleRepository(db)
        self.upload_root = Path(settings.UPLOAD_DIR)

    def list_attachments(
        self, *, organization_id: int, incident_id: int, requester: User
    ) -> list[IncidentAttachmentResponse]:
        self._require_member(requester, organization_id)
        self._get_incident(organization_id, incident_id)
        return [
            self._to_response(a) for a in self.attachments.list_for_incident(incident_id)
        ]

    async def upload(
        self,
        *,
        organization_id: int,
        incident_id: int,
        requester: User,
        file: UploadFile,
    ) -> IncidentAttachmentResponse:
        self._require_member(requester, organization_id)
        self._get_incident(organization_id, incident_id)

        org_dir = self.upload_root / str(organization_id) / str(incident_id)
        org_dir.mkdir(parents=True, exist_ok=True)

        safe_name = file.filename or "upload.bin"
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        dest = org_dir / stored_name

        content = await file.read()
        dest.write_bytes(content)

        attachment = IncidentAttachment(
            incident_id=incident_id,
            uploaded_by_user_id=requester.id,
            filename=safe_name,
            content_type=file.content_type,
            file_size=len(content),
            storage_path=str(dest),
        )
        self.attachments.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return self._to_response(attachment)

    def get_path(
        self, *, organization_id: int, incident_id: int, attachment_id: int, requester: User
    ) -> tuple[IncidentAttachment, Path]:
        self._require_member(requester, organization_id)
        self._get_incident(organization_id, incident_id)
        attachment = self.attachments.get(attachment_id)
        if attachment is None or attachment.incident_id != incident_id:
            raise NotFoundError("Attachment not found")
        path = Path(attachment.storage_path)
        if not path.exists():
            raise NotFoundError("Attachment file missing on disk")
        return attachment, path

    def delete(
        self, *, organization_id: int, incident_id: int, attachment_id: int, requester: User
    ) -> None:
        attachment, path = self.get_path(
            organization_id=organization_id,
            incident_id=incident_id,
            attachment_id=attachment_id,
            requester=requester,
        )
        if path.exists():
            path.unlink()
        self.db.delete(attachment)
        self.db.commit()

    def _get_incident(self, organization_id: int, incident_id: int):
        incident = self.incidents.get(incident_id)
        if incident is None or incident.organization_id != organization_id:
            raise NotFoundError("Incident not found")
        return incident

    def _require_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")

    def _to_response(self, attachment: IncidentAttachment) -> IncidentAttachmentResponse:
        return IncidentAttachmentResponse(
            id=attachment.id,
            incident_id=attachment.incident_id,
            filename=attachment.filename,
            content_type=attachment.content_type,
            file_size=attachment.file_size,
            uploaded_by_user_id=attachment.uploaded_by_user_id,
            created_at=attachment.created_at,
        )
