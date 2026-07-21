from fastapi import APIRouter

from app.api.v1.endpoints import auth, alerts, infrastructure, incidents, monitoring, notifications, organizations, projects, roles, teams, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(teams.router)
api_router.include_router(projects.router)
api_router.include_router(infrastructure.router)
api_router.include_router(monitoring.router)
api_router.include_router(alerts.router)
api_router.include_router(incidents.router)
api_router.include_router(notifications.router)
api_router.include_router(roles.router)
