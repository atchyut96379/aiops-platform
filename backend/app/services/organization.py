from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.enums import RoleName
from app.models.organization import Organization
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.role import UserRoleRepository
from app.schemas.organization import OrganizationUpdate
from app.utils.slug import slugify


class OrganizationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orgs = OrganizationRepository(db)
        self.memberships = UserRoleRepository(db)

    def get_for_user(self, user: User, organization_id: int | None = None) -> Organization:
        org_id = organization_id or user.default_organization_id
        if org_id is None:
            raise NotFoundError("No organization associated with this user")

        org = self.orgs.get(org_id)
        if org is None:
            raise NotFoundError("Organization not found")

        if not user.is_superuser:
            memberships = self.memberships.list_for_user_org(user.id, org.id)
            if not memberships:
                raise ForbiddenError("Not a member of this organization")
        return org

    def update(
        self,
        user: User,
        payload: OrganizationUpdate,
        organization_id: int | None = None,
    ) -> Organization:
        org = self.get_for_user(user, organization_id)
        self._require_org_admin(user, org.id)

        data = payload.model_dump(exclude_unset=True)
        if "subscription_plan" in data and data["subscription_plan"] is not None:
            data["subscription_plan"] = data["subscription_plan"].value

        if "name" in data and data["name"] != org.name:
            new_slug = slugify(data["name"])
            existing = self.orgs.get_by_slug(new_slug)
            if existing and existing.id != org.id:
                raise ConflictError("Organization name is already taken")
            org.slug = new_slug

        for key, value in data.items():
            setattr(org, key, value)

        self.db.commit()
        self.db.refresh(org)
        return org

    def _require_org_admin(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        memberships = self.memberships.list_for_user_org(user.id, organization_id)
        role_names = {m.role.name for m in memberships if m.role}
        if RoleName.ORGANIZATION_ADMIN.value not in role_names:
            raise ForbiddenError("Organization admin role required")
