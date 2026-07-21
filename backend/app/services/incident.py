from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.enums import IncidentSeverity, IncidentStatus, RoleName
from app.models.incident import Incident
from app.models.infrastructure_asset import InfrastructureAsset
from app.models.user import User
from app.repositories.audit import AuditLogRepository
from app.repositories.incident import IncidentRepository
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.role import UserRoleRepository
from app.repositories.user import UserRepository
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate


class IncidentService:
    CREATE_ROLES = set()
    UPDATE_ROLES = {
        RoleName.ORGANIZATION_ADMIN.value,
        RoleName.SUPPORT_ENGINEER.value,
        RoleName.SUPER_ADMIN.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.incidents = IncidentRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.memberships = UserRoleRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditLogRepository(db)

    def create_incident(
        self,
        *,
        organization_id: int,
        payload: IncidentCreate,
        requester: User,
    ) -> IncidentResponse:
        self._require_org_member(requester, organization_id)
        asset = None
        if payload.asset_id is not None:
            asset = self._get_asset_or_404(organization_id, payload.asset_id)

        incident = Incident(
            organization_id=organization_id,
            asset_id=asset.id if asset is not None else None,
            incident_type=payload.incident_type,
            title=payload.title,
            description=payload.description,
            severity=payload.severity.value,
            status=IncidentStatus.OPEN.value,
        )
        incident.details = payload.details
        self.incidents.add(incident)
        self.audit.record(
            action="incident.created",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="incident",
            resource_id=str(incident.id),
            details={
                "asset_id": incident.asset_id,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
            },
        )
        self.db.commit()
        self.db.refresh(incident)
        return self._to_response(incident)

    def list_incidents(
        self,
        *,
        organization_id: int,
        requester: User,
        asset_id: int | None = None,
        status: str | None = None,
        severity: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[IncidentResponse]:
        self._require_org_member(requester, organization_id)
        incidents = self.incidents.list_for_organization(
            organization_id=organization_id,
            asset_id=asset_id,
            status=status,
            severity=severity,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(item) for item in incidents]

    def get_incident(
        self, *, organization_id: int, incident_id: int, requester: User
    ) -> IncidentResponse:
        self._require_org_member(requester, organization_id)
        incident = self.incidents.get(incident_id)
        if incident is None or incident.organization_id != organization_id:
            raise NotFoundError("Incident not found")
        return self._to_response(incident)

    def update_incident(
        self,
        *,
        organization_id: int,
        incident_id: int,
        payload: IncidentUpdate,
        requester: User,
        roles: list[str],
    ) -> IncidentResponse:
        self._require_update_access(requester, organization_id, roles)
        incident = self.incidents.get(incident_id)
        if incident is None or incident.organization_id != organization_id:
            raise NotFoundError("Incident not found")

        data = payload.model_dump(exclude_unset=True)
        if "status" in data and data["status"] is not None:
            data["status"] = data["status"].value
        if "severity" in data and data["severity"] is not None:
            data["severity"] = data["severity"].value
        if "assignee_user_id" in data and data["assignee_user_id"] is not None:
            assignee = self.users.get(data["assignee_user_id"])
            if assignee is None:
                raise NotFoundError("Assignee user not found")

        details = data.pop("details", None)
        for key, value in data.items():
            setattr(incident, key, value)
        if details is not None:
            incident.details = details

        self.audit.record(
            action="incident.updated",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="incident",
            resource_id=str(incident.id),
            details={"updated_fields": list(data.keys())},
        )
        self.db.commit()
        self.db.refresh(incident)
        return self._to_response(incident)

    def _get_asset_or_404(self, organization_id: int, asset_id: int) -> InfrastructureAsset:
        asset = self.assets.get(asset_id)
        if asset is None or asset.organization_id != organization_id or not asset.is_active:
            raise NotFoundError("Infrastructure asset not found")
        return asset

    def _require_org_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")

    def _require_update_access(
        self, user: User, organization_id: int, roles: list[str]
    ) -> None:
        self._require_org_member(user, organization_id)
        if user.is_superuser or RoleName.SUPER_ADMIN.value in roles:
            return
        if not self.UPDATE_ROLES.intersection(roles):
            raise ForbiddenError("Insufficient permissions to update incidents")

    def _to_response(self, incident: Incident) -> IncidentResponse:
        return IncidentResponse(
            id=incident.id,
            organization_id=incident.organization_id,
            asset_id=incident.asset_id,
            incident_type=incident.incident_type,
            title=incident.title,
            description=incident.description,
            severity=incident.severity,
            status=incident.status,
            assignee_user_id=incident.assignee_user_id,
            resolution=incident.resolution,
            details=incident.details,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
        )
