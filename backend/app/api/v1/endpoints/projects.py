from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.security.rbac import require_roles
from app.services.project import ProjectService

router = APIRouter(prefix="/organizations/me/projects", tags=["Projects"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("", response_model=list[ProjectResponse], summary="List projects")
def list_projects(
    db: DbSession,
    current: AuthenticatedUser,
    team_id: int | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[ProjectResponse]:
    return ProjectService(db).list_projects(
        organization_id=_org_id(current),
        requester=current.user,
        team_id=team_id,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
)
def create_project(
    payload: ProjectCreate,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(
            RoleName.ORGANIZATION_ADMIN,
            RoleName.DEVOPS_ENGINEER,
            RoleName.CLOUD_ENGINEER,
            RoleName.SUPER_ADMIN,
        )
    ),
) -> ProjectResponse:
    return ProjectService(db).create_project(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
    )


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project")
def get_project(
    project_id: int, db: DbSession, current: AuthenticatedUser
) -> ProjectResponse:
    return ProjectService(db).get_project(
        organization_id=_org_id(current),
        project_id=project_id,
        requester=current.user,
    )


@router.patch("/{project_id}", response_model=ProjectResponse, summary="Update project")
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(
            RoleName.ORGANIZATION_ADMIN,
            RoleName.DEVOPS_ENGINEER,
            RoleName.CLOUD_ENGINEER,
            RoleName.SUPER_ADMIN,
        )
    ),
) -> ProjectResponse:
    return ProjectService(db).update_project(
        organization_id=_org_id(current),
        project_id=project_id,
        payload=payload,
        requester=current.user,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete project")
def delete_project(
    project_id: int,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> None:
    ProjectService(db).delete_project(
        organization_id=_org_id(current),
        project_id=project_id,
        requester=current.user,
    )
