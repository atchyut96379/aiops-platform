import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.cloud_integration import CloudIntegration
from app.models.enums import RoleName
from app.models.user import User
from app.repositories.cloud_integration import CloudIntegrationRepository
from app.repositories.infrastructure_asset import InfrastructureAssetRepository
from app.repositories.role import UserRoleRepository
from app.schemas.integration import CloudIntegrationCreate, CloudIntegrationResponse, CloudSyncResult
from app.services.cloud.aws import discover_aws_ec2_instances
from app.services.cloud.azure import discover_azure_vms
from app.services.cloud.gcp import discover_gcp_vms
from app.services.infrastructure import InfrastructureService


class CloudIntegrationService:
    WRITE_ROLES = {
        RoleName.ORGANIZATION_ADMIN.value,
        RoleName.CLOUD_ENGINEER.value,
        RoleName.SUPER_ADMIN.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.integrations = CloudIntegrationRepository(db)
        self.assets = InfrastructureAssetRepository(db)
        self.memberships = UserRoleRepository(db)

    def list_integrations(
        self, *, organization_id: int, requester: User
    ) -> list[CloudIntegrationResponse]:
        self._require_member(requester, organization_id)
        items = self.integrations.list_for_organization(organization_id)
        return [CloudIntegrationResponse.model_validate(i) for i in items]

    def create_integration(
        self,
        *,
        organization_id: int,
        payload: CloudIntegrationCreate,
        requester: User,
        roles: list[str],
    ) -> CloudIntegrationResponse:
        self._require_write_access(requester, organization_id, roles)
        if payload.provider not in {"aws", "azure", "gcp"}:
            raise ValidationAppError("Provider must be aws, azure, or gcp")

        integration = CloudIntegration(
            organization_id=organization_id,
            provider=payload.provider,
            name=payload.name.strip(),
            credentials_json=json.dumps(payload.credentials) if payload.credentials else None,
        )
        self.integrations.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        return CloudIntegrationResponse.model_validate(integration)

    def sync_integration(
        self,
        *,
        organization_id: int,
        integration_id: int,
        requester: User,
        roles: list[str],
    ) -> CloudSyncResult:
        self._require_write_access(requester, organization_id, roles)
        integration = self.integrations.get(integration_id)
        if integration is None or integration.organization_id != organization_id:
            raise NotFoundError("Integration not found")

        integration.sync_status = "syncing"
        self.db.flush()

        credentials = {}
        if integration.credentials_json:
            try:
                credentials = json.loads(integration.credentials_json)
            except json.JSONDecodeError:
                credentials = {}

        discovered = self._discover_assets(integration, credentials)
        imported = InfrastructureService(self.db).upsert_cloud_assets(
            organization_id=organization_id,
            discovered=discovered,
            requester=requester,
        )

        integration.sync_status = "completed"
        integration.last_sync_at = datetime.now(timezone.utc)
        integration.integration_metadata = {
            **integration.integration_metadata,
            "last_discovered_count": len(discovered),
            "last_imported_count": imported,
            "discovered": discovered,
        }
        self.db.commit()
        return CloudSyncResult(
            integration_id=integration.id,
            provider=integration.provider,
            assets_discovered=len(discovered),
            assets_imported=imported,
            assets=discovered,
            message=(
                f"Sync completed for {integration.provider} '{integration.name}': "
                f"{len(discovered)} discovered, {imported} imported to inventory"
            ),
        )

    def _discover_assets(
        self, integration: CloudIntegration, credentials: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if integration.provider == "aws":
            return discover_aws_ec2_instances(credentials, credentials.get("region"))
        if integration.provider == "azure":
            return discover_azure_vms(credentials)
        return discover_gcp_vms(credentials)

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
            raise ForbiddenError("Insufficient permissions to manage cloud integrations")
