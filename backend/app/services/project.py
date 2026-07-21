from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.project import Project
from app.models.user import User
from app.repositories.audit import AuditLogRepository
from app.repositories.project import ProjectRepository
from app.repositories.role import UserRoleRepository
from app.repositories.team import TeamRepository
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.utils.slug import slugify


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.teams = TeamRepository(db)
        self.memberships = UserRoleRepository(db)
        self.audit = AuditLogRepository(db)

    def list_projects(
        self,
        *,
        organization_id: int,
        requester: User,
        team_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ProjectResponse]:
        self._require_org_member(requester, organization_id)
        projects = self.projects.list_for_organization(
            organization_id, team_id=team_id, skip=skip, limit=limit
        )
        return [ProjectResponse.model_validate(p) for p in projects]

    def get_project(
        self, *, organization_id: int, project_id: int, requester: User
    ) -> ProjectResponse:
        self._require_org_member(requester, organization_id)
        project = self._get_project_or_404(organization_id, project_id)
        return ProjectResponse.model_validate(project)

    def create_project(
        self, *, organization_id: int, payload: ProjectCreate, requester: User
    ) -> ProjectResponse:
        self._require_org_member(requester, organization_id)
        if payload.team_id is not None:
            team = self.teams.get(payload.team_id)
            if team is None or team.organization_id != organization_id:
                raise NotFoundError("Team not found")

        slug = slugify(payload.name)
        if self.projects.get_by_slug(organization_id, slug):
            raise ConflictError("Project name is already taken in this organization")

        project = Project(
            organization_id=organization_id,
            team_id=payload.team_id,
            name=payload.name,
            slug=slug,
            description=payload.description,
            environment=payload.environment.value,
        )
        self.projects.add(project)
        self.audit.record(
            action="project.created",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="project",
            resource_id=str(project.id),
        )
        self.db.commit()
        self.db.refresh(project)
        return ProjectResponse.model_validate(project)

    def update_project(
        self,
        *,
        organization_id: int,
        project_id: int,
        payload: ProjectUpdate,
        requester: User,
    ) -> ProjectResponse:
        self._require_org_member(requester, organization_id)
        project = self._get_project_or_404(organization_id, project_id)
        data = payload.model_dump(exclude_unset=True)

        if "environment" in data and data["environment"] is not None:
            data["environment"] = data["environment"].value

        if "team_id" in data and data["team_id"] is not None:
            team = self.teams.get(data["team_id"])
            if team is None or team.organization_id != organization_id:
                raise NotFoundError("Team not found")

        if "name" in data and data["name"] != project.name:
            new_slug = slugify(data["name"])
            existing = self.projects.get_by_slug(organization_id, new_slug)
            if existing and existing.id != project.id:
                raise ConflictError("Project name is already taken in this organization")
            project.slug = new_slug

        for key, value in data.items():
            setattr(project, key, value)

        self.audit.record(
            action="project.updated",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="project",
            resource_id=str(project.id),
        )
        self.db.commit()
        self.db.refresh(project)
        return ProjectResponse.model_validate(project)

    def delete_project(
        self, *, organization_id: int, project_id: int, requester: User
    ) -> None:
        self._require_org_member(requester, organization_id)
        project = self._get_project_or_404(organization_id, project_id)
        project.is_active = False
        self.audit.record(
            action="project.deleted",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="project",
            resource_id=str(project.id),
        )
        self.db.commit()

    def _get_project_or_404(self, organization_id: int, project_id: int) -> Project:
        project = self.projects.get(project_id)
        if project is None or project.organization_id != organization_id or not project.is_active:
            raise NotFoundError("Project not found")
        return project

    def _require_org_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")
