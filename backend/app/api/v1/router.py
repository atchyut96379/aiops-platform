from fastapi import APIRouter

from app.api.v1.endpoints import auth, infrastructure, organizations, projects, roles, teams, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(teams.router)
api_router.include_router(projects.router)
api_router.include_router(infrastructure.router)
api_router.include_router(roles.router)
