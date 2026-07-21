from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.enums import RoleName
from app.models.infrastructure_asset import InfrastructureAsset
from app.models.user import User
from app.repositories.audit import AuditLogRepository
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.project import ProjectRepository
from app.repositories.role import UserRoleRepository
from app.repositories.user import UserRepository
from app.schemas.infrastructure import (
    InfrastructureAssetCreate,
    InfrastructureAssetResponse,
    InfrastructureAssetStats,
    InfrastructureAssetUpdate,
)


class InfrastructureService:
    WRITE_ROLES = {
        RoleName.ORGANIZATION_ADMIN.value,
        RoleName.DEVOPS_ENGINEER.value,
        RoleName.CLOUD_ENGINEER.value,
        RoleName.SUPER_ADMIN.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.assets = InfrastructureAssetRepository(db)
        self.projects = ProjectRepository(db)
        self.users = UserRepository(db)
        self.memberships = UserRoleRepository(db)
        self.audit = AuditLogRepository(db)

    def list_assets(
        self,
        *,
        organization_id: int,
        requester: User,
        asset_type: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        project_id: int | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[InfrastructureAssetResponse]:
        self._require_org_member(requester, organization_id)
        assets = self.assets.list_for_organization(
            organization_id,
            asset_type=asset_type,
            environment=environment,
            status=status,
            project_id=project_id,
            search=search,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(a) for a in assets]

    def get_asset(
        self, *, organization_id: int, asset_id: int, requester: User
    ) -> InfrastructureAssetResponse:
        self._require_org_member(requester, organization_id)
        asset = self._get_asset_or_404(organization_id, asset_id)
        return self._to_response(asset)

    def create_asset(
        self,
        *,
        organization_id: int,
        payload: InfrastructureAssetCreate,
        requester: User,
        roles: list[str],
    ) -> InfrastructureAssetResponse:
        self._require_write_access(requester, organization_id, roles)
        if self.assets.get_by_hostname(organization_id, payload.hostname):
            raise ConflictError("Hostname already registered in this organization")

        if payload.project_id is not None:
            project = self.projects.get(payload.project_id)
            if project is None or project.organization_id != organization_id:
                raise NotFoundError("Project not found")

        if payload.owner_user_id is not None:
            owner = self.users.get(payload.owner_user_id)
            if owner is None:
                raise NotFoundError("Owner user not found")

        asset = InfrastructureAsset(
            organization_id=organization_id,
            project_id=payload.project_id,
            asset_type=payload.asset_type.value,
            hostname=payload.hostname,
            ip_address=payload.ip_address,
            os=payload.os,
            environment=payload.environment.value,
            owner_user_id=payload.owner_user_id,
            status=payload.status.value,
        )
        asset.tags_list = payload.tags
        asset.metadata_dict = payload.metadata
        self.assets.add(asset)
        self.audit.record(
            action="asset.created",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="infrastructure_asset",
            resource_id=str(asset.id),
            details={"hostname": asset.hostname, "asset_type": asset.asset_type},
        )
        self.db.commit()
        self.db.refresh(asset)
        return self._to_response(asset)

    def update_asset(
        self,
        *,
        organization_id: int,
        asset_id: int,
        payload: InfrastructureAssetUpdate,
        requester: User,
        roles: list[str],
    ) -> InfrastructureAssetResponse:
        self._require_write_access(requester, organization_id, roles)
        asset = self._get_asset_or_404(organization_id, asset_id)
        data = payload.model_dump(exclude_unset=True)

        if "asset_type" in data and data["asset_type"] is not None:
            data["asset_type"] = data["asset_type"].value
        if "environment" in data and data["environment"] is not None:
            data["environment"] = data["environment"].value
        if "status" in data and data["status"] is not None:
            data["status"] = data["status"].value

        if "hostname" in data and data["hostname"] != asset.hostname:
            existing = self.assets.get_by_hostname(organization_id, data["hostname"])
            if existing and existing.id != asset.id:
                raise ConflictError("Hostname already registered in this organization")

        if "project_id" in data and data["project_id"] is not None:
            project = self.projects.get(data["project_id"])
            if project is None or project.organization_id != organization_id:
                raise NotFoundError("Project not found")

        if "owner_user_id" in data and data["owner_user_id"] is not None:
            owner = self.users.get(data["owner_user_id"])
            if owner is None:
                raise NotFoundError("Owner user not found")

        tags = data.pop("tags", None)
        metadata = data.pop("metadata", None)
        for key, value in data.items():
            setattr(asset, key, value)
        if tags is not None:
            asset.tags_list = tags
        if metadata is not None:
            asset.metadata_dict = metadata

        self.audit.record(
            action="asset.updated",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="infrastructure_asset",
            resource_id=str(asset.id),
        )
        self.db.commit()
        self.db.refresh(asset)
        return self._to_response(asset)

    def delete_asset(
        self,
        *,
        organization_id: int,
        asset_id: int,
        requester: User,
        roles: list[str],
    ) -> None:
        self._require_write_access(requester, organization_id, roles)
        asset = self._get_asset_or_404(organization_id, asset_id)
        asset.is_active = False
        self.audit.record(
            action="asset.deleted",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="infrastructure_asset",
            resource_id=str(asset.id),
        )
        self.db.commit()

    def get_stats(self, *, organization_id: int, requester: User) -> InfrastructureAssetStats:
        self._require_org_member(requester, organization_id)
        return InfrastructureAssetStats(
            total=self.assets.count_for_organization(organization_id),
            by_type={row[0]: row[1] for row in self.assets.stats_by_type(organization_id)},
            by_status={row[0]: row[1] for row in self.assets.stats_by_status(organization_id)},
        )

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

    def _require_write_access(
        self, user: User, organization_id: int, roles: list[str]
    ) -> None:
        self._require_org_member(user, organization_id)
        if user.is_superuser or RoleName.SUPER_ADMIN.value in roles:
            return
        if not self.WRITE_ROLES.intersection(roles):
            raise ForbiddenError("Insufficient permissions to modify infrastructure assets")

    def _to_response(self, asset: InfrastructureAsset) -> InfrastructureAssetResponse:
        return InfrastructureAssetResponse(
            id=asset.id,
            organization_id=asset.organization_id,
            project_id=asset.project_id,
            asset_type=asset.asset_type,
            hostname=asset.hostname,
            ip_address=asset.ip_address,
            os=asset.os,
            environment=asset.environment,
            owner_user_id=asset.owner_user_id,
            tags=asset.tags_list,
            status=asset.status,
            metadata=asset.metadata_dict,
            is_active=asset.is_active,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )
