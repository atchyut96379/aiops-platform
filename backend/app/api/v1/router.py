from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    ai,
    alert_rules,
    alerts,
    audit,
    auth,
    billing,
    dashboard,
    infrastructure,
    incidents,
    logs,
    monitoring,
    notifications,
    organizations,
    projects,
    roles,
    teams,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(teams.router)
api_router.include_router(projects.router)
api_router.include_router(infrastructure.router)
api_router.include_router(monitoring.router)
api_router.include_router(alerts.router)
api_router.include_router(alert_rules.router)
api_router.include_router(incidents.router)
api_router.include_router(notifications.router)
api_router.include_router(roles.router)
api_router.include_router(dashboard.router)
api_router.include_router(audit.router)
api_router.include_router(ai.router)
api_router.include_router(agents.router)
api_router.include_router(agents.agent_router)
api_router.include_router(logs.router)
api_router.include_router(billing.router)
