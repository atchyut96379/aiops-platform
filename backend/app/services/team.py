from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.team import Team, TeamMember
from app.models.user import User
from app.repositories.audit import AuditLogRepository
from app.repositories.role import UserRoleRepository
from app.repositories.team import TeamMemberRepository, TeamRepository
from app.repositories.user import UserRepository
from app.schemas.team import TeamCreate, TeamMemberResponse, TeamResponse, TeamUpdate
from app.utils.slug import slugify


class TeamService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.teams = TeamRepository(db)
        self.team_members = TeamMemberRepository(db)
        self.memberships = UserRoleRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditLogRepository(db)

    def list_teams(
        self, *, organization_id: int, requester: User, skip: int = 0, limit: int = 50
    ) -> list[TeamResponse]:
        self._require_org_member(requester, organization_id)
        teams = self.teams.list_for_organization(organization_id, skip=skip, limit=limit)
        return [self._to_response(team) for team in teams]

    def get_team(self, *, organization_id: int, team_id: int, requester: User) -> TeamResponse:
        self._require_org_member(requester, organization_id)
        team = self._get_team_or_404(organization_id, team_id)
        return self._to_response(team)

    def create_team(
        self, *, organization_id: int, payload: TeamCreate, requester: User
    ) -> TeamResponse:
        self._require_org_member(requester, organization_id)
        slug = slugify(payload.name)
        if self.teams.get_by_slug(organization_id, slug):
            raise ConflictError("Team name is already taken in this organization")

        team = Team(
            organization_id=organization_id,
            name=payload.name,
            slug=slug,
            description=payload.description,
        )
        self.teams.add(team)
        self.audit.record(
            action="team.created",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="team",
            resource_id=str(team.id),
        )
        self.db.commit()
        self.db.refresh(team)
        return self._to_response(team)

    def update_team(
        self,
        *,
        organization_id: int,
        team_id: int,
        payload: TeamUpdate,
        requester: User,
    ) -> TeamResponse:
        self._require_org_member(requester, organization_id)
        team = self._get_team_or_404(organization_id, team_id)
        data = payload.model_dump(exclude_unset=True)

        if "name" in data and data["name"] != team.name:
            new_slug = slugify(data["name"])
            existing = self.teams.get_by_slug(organization_id, new_slug)
            if existing and existing.id != team.id:
                raise ConflictError("Team name is already taken in this organization")
            team.slug = new_slug

        for key, value in data.items():
            setattr(team, key, value)

        self.audit.record(
            action="team.updated",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="team",
            resource_id=str(team.id),
        )
        self.db.commit()
        self.db.refresh(team)
        return self._to_response(team)

    def delete_team(self, *, organization_id: int, team_id: int, requester: User) -> None:
        self._require_org_member(requester, organization_id)
        team = self._get_team_or_404(organization_id, team_id)
        team.is_active = False
        self.audit.record(
            action="team.deleted",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="team",
            resource_id=str(team.id),
        )
        self.db.commit()

    def list_members(
        self, *, organization_id: int, team_id: int, requester: User
    ) -> list[TeamMemberResponse]:
        self._require_org_member(requester, organization_id)
        team = self._get_team_or_404(organization_id, team_id)
        return [self._member_to_response(m) for m in team.members]

    def add_member(
        self, *, organization_id: int, team_id: int, user_id: int, requester: User
    ) -> TeamMemberResponse:
        self._require_org_member(requester, organization_id)
        team = self._get_team_or_404(organization_id, team_id)
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found")

        org_memberships = self.memberships.list_for_user_org(user_id, organization_id)
        if not org_memberships and not user.is_superuser:
            raise ForbiddenError("User must be an organization member before joining a team")

        if self.team_members.get_membership(team.id, user_id):
            raise ConflictError("User is already a team member")

        member = TeamMember(team_id=team.id, user_id=user_id)
        self.team_members.add(member)
        self.audit.record(
            action="team.member_added",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="team",
            resource_id=str(team.id),
            details={"user_id": user_id},
        )
        self.db.commit()
        self.db.refresh(member)
        return self._member_to_response(member)

    def remove_member(
        self, *, organization_id: int, team_id: int, user_id: int, requester: User
    ) -> None:
        self._require_org_member(requester, organization_id)
        team = self._get_team_or_404(organization_id, team_id)
        member = self.team_members.get_membership(team.id, user_id)
        if member is None:
            raise NotFoundError("Team member not found")
        self.db.delete(member)
        self.audit.record(
            action="team.member_removed",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="team",
            resource_id=str(team.id),
            details={"user_id": user_id},
        )
        self.db.commit()

    def _get_team_or_404(self, organization_id: int, team_id: int) -> Team:
        team = self.teams.get(team_id)
        if team is None or team.organization_id != organization_id or not team.is_active:
            raise NotFoundError("Team not found")
        return team

    def _require_org_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")

    def _to_response(self, team: Team) -> TeamResponse:
        return TeamResponse(
            id=team.id,
            organization_id=team.organization_id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            is_active=team.is_active,
            member_count=len(team.members),
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    def _member_to_response(self, member: TeamMember) -> TeamMemberResponse:
        user = member.user
        return TeamMemberResponse(
            id=member.id,
            team_id=member.team_id,
            user_id=member.user_id,
            user_email=user.email if user else "",
            user_name=user.full_name if user else "",
            created_at=member.created_at,
        )
