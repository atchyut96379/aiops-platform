from fastapi import APIRouter

from app.api.v1.deps import AuthenticatedUser, DbSession
from app.schemas.role import RoleResponse
from app.services.role import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleResponse], summary="List system roles")
def list_roles(db: DbSession, _: AuthenticatedUser) -> list[RoleResponse]:
    roles = RoleService(db).list_roles()
    return [RoleResponse.model_validate(role) for role in roles]
