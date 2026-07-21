from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.notification import (
    NotificationChannelCreate,
    NotificationChannelResponse,
    NotificationChannelUpdate,
    NotificationLogResponse,
)
from app.security.rbac import require_roles
from app.services.notification import NotificationChannelService

router = APIRouter(prefix="/organizations/me", tags=["Notifications"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get(
    "/notification-channels",
    response_model=list[NotificationChannelResponse],
    summary="List notification channels",
)
def list_channels(
    db: DbSession,
    current: AuthenticatedUser,
    active_only: bool = Query(default=False),
) -> list[NotificationChannelResponse]:
    return NotificationChannelService(db).list_channels(
        organization_id=_org_id(current),
        requester=current.user,
        active_only=active_only,
    )


@router.post(
    "/notification-channels",
    response_model=NotificationChannelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create notification channel",
)
def create_channel(
    payload: NotificationChannelCreate,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> NotificationChannelResponse:
    return NotificationChannelService(db).create_channel(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.get(
    "/notification-logs",
    response_model=list[NotificationLogResponse],
    summary="List notification delivery logs",
)
def list_notification_logs(
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[NotificationLogResponse]:
    return NotificationChannelService(db).list_logs(
        organization_id=_org_id(current),
        requester=current.user,
        skip=skip,
        limit=limit,
    )


@router.patch(
    "/notification-channels/{channel_id}",
    response_model=NotificationChannelResponse,
    summary="Update notification channel",
)
def update_channel(
    channel_id: int,
    payload: NotificationChannelUpdate,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> NotificationChannelResponse:
    return NotificationChannelService(db).update_channel(
        organization_id=_org_id(current),
        channel_id=channel_id,
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.delete(
    "/notification-channels/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate notification channel",
)
def delete_channel(
    channel_id: int,
    db: DbSession,
    current: CurrentUser = Depends(
        require_roles(RoleName.ORGANIZATION_ADMIN, RoleName.SUPER_ADMIN)
    ),
) -> None:
    NotificationChannelService(db).delete_channel(
        organization_id=_org_id(current),
        channel_id=channel_id,
        requester=current.user,
        roles=current.roles,
    )
