from typing import Callable, Iterable

from fastapi import Depends

from app.api.v1.deps import CurrentUser, get_current_user
from app.core.exceptions import ForbiddenError
from app.models.enums import RoleName


def require_roles(*allowed: RoleName | str) -> Callable:
    allowed_values = {
        role.value if isinstance(role, RoleName) else role for role in allowed
    }

    def dependency(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current.is_superuser or RoleName.SUPER_ADMIN.value in current.roles:
            return current
        if not allowed_values.intersection(current.roles):
            raise ForbiddenError(
                "Insufficient role permissions",
                code="insufficient_role",
                details={"required": sorted(allowed_values), "actual": current.roles},
            )
        return current

    return dependency


def require_any_authenticated(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current


ADMIN_ROLES: Iterable[RoleName] = (
    RoleName.SUPER_ADMIN,
    RoleName.ORGANIZATION_ADMIN,
)
