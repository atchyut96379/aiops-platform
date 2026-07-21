from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.team import TeamCreate, TeamMemberAdd, TeamMemberResponse, TeamResponse, TeamUpdate
from app.security.rbac import require_roles
from app.services.team import TeamService

router = APIRouter(prefix="/organizations/me/teams", tags=["Teams"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("", response_model=list[TeamResponse], summary="List teams")
def list_teams(
    db: DbSession,
    current: AuthenticatedUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[TeamResponse]:
    return TeamService(db).list_teams(
        organization_id=_org_id(current),
        requester=current.user,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED, summary="Create team")
def create_team(
    payload: TeamCreate,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(
            RoleName.ORGANIZATION_ADMIN,
            RoleName.DEVOPS_ENGINEER,
            RoleName.SUPER_ADMIN,
        )
    ),
) -> TeamResponse:
    return TeamService(db).create_team(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
    )


@router.get("/{team_id}", response_model=TeamResponse, summary="Get team")
def get_team(team_id: int, db: DbSession, current: AuthenticatedUser) -> TeamResponse:
    return TeamService(db).get_team(
        organization_id=_org_id(current),
        team_id=team_id,
        requester=current.user,
    )


@router.patch("/{team_id}", response_model=TeamResponse, summary="Update team")
def update_team(
    team_id: int,
    payload: TeamUpdate,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> TeamResponse:
    return TeamService(db).update_team(
        organization_id=_org_id(current),
        team_id=team_id,
        payload=payload,
        requester=current.user,
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete team")
def delete_team(
    team_id: int,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> None:
    TeamService(db).delete_team(
        organization_id=_org_id(current),
        team_id=team_id,
        requester=current.user,
    )


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse], summary="List team members")
def list_team_members(
    team_id: int, db: DbSession, current: AuthenticatedUser
) -> list[TeamMemberResponse]:
    return TeamService(db).list_members(
        organization_id=_org_id(current),
        team_id=team_id,
        requester=current.user,
    )


@router.post(
    "/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add team member",
)
def add_team_member(
    team_id: int,
    payload: TeamMemberAdd,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.DEVOPS_ENGINEER, RoleName.SUPER_ADMIN)
    ),
) -> TeamMemberResponse:
    return TeamService(db).add_member(
        organization_id=_org_id(current),
        team_id=team_id,
        user_id=payload.user_id,
        requester=current.user,
    )


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove team member",
)
def remove_team_member(
    team_id: int,
    user_id: int,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.DEVOPS_ENGINEER, RoleName.SUPER_ADMIN)
    ),
) -> None:
    TeamService(db).remove_member(
        organization_id=_org_id(current),
        team_id=team_id,
        user_id=user_id,
        requester=current.user,
    )
