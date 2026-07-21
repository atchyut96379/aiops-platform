import json
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.models.alert import Alert
from app.models.enums import ALERT_LEVEL_RANK, AlertLevel, NotificationChannelType, NotificationStatus, RoleName
from app.models.notification import NotificationChannel, NotificationLog
from app.models.user import User
from app.repositories.audit import AuditLogRepository
from app.repositories.notification import NotificationChannelRepository, NotificationLogRepository
from app.repositories.role import UserRoleRepository
from app.schemas.notification import (
    NotificationChannelCreate,
    NotificationChannelResponse,
    NotificationChannelUpdate,
    NotificationLogResponse,
)
from app.services.email import EmailService

logger = get_logger(__name__)


class NotificationChannelService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.channels = NotificationChannelRepository(db)
        self.logs = NotificationLogRepository(db)
        self.memberships = UserRoleRepository(db)
        self.audit = AuditLogRepository(db)

    def list_channels(
        self, *, organization_id: int, requester: User, active_only: bool = False
    ) -> list[NotificationChannelResponse]:
        self._require_org_member(requester, organization_id)
        items = self.channels.list_for_organization(
            organization_id, active_only=active_only
        )
        return [self._channel_response(c) for c in items]

    def create_channel(
        self,
        *,
        organization_id: int,
        payload: NotificationChannelCreate,
        requester: User,
        roles: list[str],
    ) -> NotificationChannelResponse:
        self._require_admin(requester, organization_id, roles)
        channel = NotificationChannel(
            organization_id=organization_id,
            name=payload.name,
            channel_type=payload.channel_type.value,
            min_alert_level=payload.min_alert_level.value,
            is_active=payload.is_active,
        )
        channel.config = payload.config
        self.channels.add(channel)
        self.audit.record(
            action="notification_channel.created",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="notification_channel",
            resource_id=str(channel.id),
        )
        self.db.commit()
        self.db.refresh(channel)
        return self._channel_response(channel)

    def update_channel(
        self,
        *,
        organization_id: int,
        channel_id: int,
        payload: NotificationChannelUpdate,
        requester: User,
        roles: list[str],
    ) -> NotificationChannelResponse:
        self._require_admin(requester, organization_id, roles)
        channel = self._get_channel_or_404(organization_id, channel_id)
        data = payload.model_dump(exclude_unset=True)
        if "min_alert_level" in data and data["min_alert_level"] is not None:
            data["min_alert_level"] = data["min_alert_level"].value
        config = data.pop("config", None)
        for key, value in data.items():
            setattr(channel, key, value)
        if config is not None:
            channel.config = config
        self.audit.record(
            action="notification_channel.updated",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="notification_channel",
            resource_id=str(channel.id),
        )
        self.db.commit()
        self.db.refresh(channel)
        return self._channel_response(channel)

    def delete_channel(
        self,
        *,
        organization_id: int,
        channel_id: int,
        requester: User,
        roles: list[str],
    ) -> None:
        self._require_admin(requester, organization_id, roles)
        channel = self._get_channel_or_404(organization_id, channel_id)
        channel.is_active = False
        self.audit.record(
            action="notification_channel.deleted",
            user_id=requester.id,
            organization_id=organization_id,
            resource_type="notification_channel",
            resource_id=str(channel.id),
        )
        self.db.commit()

    def list_logs(
        self, *, organization_id: int, requester: User, skip: int = 0, limit: int = 50
    ) -> list[NotificationLogResponse]:
        self._require_org_member(requester, organization_id)
        entries = self.logs.list_for_organization(organization_id, skip=skip, limit=limit)
        return [NotificationLogResponse.model_validate(e) for e in entries]

    def _get_channel_or_404(self, organization_id: int, channel_id: int) -> NotificationChannel:
        channel = self.channels.get(channel_id)
        if channel is None or channel.organization_id != organization_id:
            raise NotFoundError("Notification channel not found")
        return channel

    def _require_org_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")

    def _require_admin(self, user: User, organization_id: int, roles: list[str]) -> None:
        self._require_org_member(user, organization_id)
        if user.is_superuser or RoleName.SUPER_ADMIN.value in roles:
            return
        if RoleName.ORGANIZATION_ADMIN.value not in roles:
            raise ForbiddenError("Organization admin role required")

    def _channel_response(self, channel: NotificationChannel) -> NotificationChannelResponse:
        return NotificationChannelResponse(
            id=channel.id,
            organization_id=channel.organization_id,
            name=channel.name,
            channel_type=channel.channel_type,
            config=channel.config,
            min_alert_level=channel.min_alert_level,
            is_active=channel.is_active,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
        )


class NotificationDispatchService:
    """Deliver alert/incident notifications through configured org channels."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.channels = NotificationChannelRepository(db)
        self.logs = NotificationLogRepository(db)
        self.email = EmailService()

    def dispatch_alert(
        self,
        *,
        organization_id: int,
        alert: Alert,
        asset_hostname: Optional[str] = None,
    ) -> list[NotificationLog]:
        message = self._format_alert_message(alert, asset_hostname)
        return self._dispatch(
            organization_id=organization_id,
            alert_level=alert.level,
            message=message,
            alert_id=alert.id,
        )

    def dispatch_incident(
        self,
        *,
        organization_id: int,
        incident_id: int,
        title: str,
        severity: str,
        description: Optional[str] = None,
    ) -> list[NotificationLog]:
        level = severity if severity in ALERT_LEVEL_RANK else AlertLevel.MEDIUM.value
        message = f"[INCIDENT] {title}\nSeverity: {severity}\n{description or ''}"
        return self._dispatch(
            organization_id=organization_id,
            alert_level=level,
            message=message,
            incident_id=incident_id,
        )

    def _dispatch(
        self,
        *,
        organization_id: int,
        alert_level: str,
        message: str,
        alert_id: Optional[int] = None,
        incident_id: Optional[int] = None,
    ) -> list[NotificationLog]:
        sent_logs: list[NotificationLog] = []
        alert_rank = ALERT_LEVEL_RANK.get(alert_level, 0)

        for channel in self.channels.list_for_organization(organization_id, active_only=True):
            min_rank = ALERT_LEVEL_RANK.get(channel.min_alert_level, 0)
            if alert_rank < min_rank:
                log = self._record_log(
                    organization_id=organization_id,
                    channel=channel,
                    alert_id=alert_id,
                    incident_id=incident_id,
                    status=NotificationStatus.SKIPPED.value,
                    message=message,
                    error="Below channel minimum alert level",
                )
                sent_logs.append(log)
                continue

            try:
                self._send(channel, message)
                log = self._record_log(
                    organization_id=organization_id,
                    channel=channel,
                    alert_id=alert_id,
                    incident_id=incident_id,
                    status=NotificationStatus.SENT.value,
                    message=message,
                )
            except Exception as exc:  # noqa: BLE001 — log delivery failures per channel
                log = self._record_log(
                    organization_id=organization_id,
                    channel=channel,
                    alert_id=alert_id,
                    incident_id=incident_id,
                    status=NotificationStatus.FAILED.value,
                    message=message,
                    error=str(exc),
                )
            sent_logs.append(log)

        self.db.commit()
        return sent_logs

    def _send(self, channel: NotificationChannel, message: str) -> None:
        config = channel.config
        channel_type = channel.channel_type

        if channel_type == NotificationChannelType.EMAIL.value:
            subject = f"{settings.APP_NAME} — Alert notification"
            for recipient in config.get("recipients", []):
                self.email.send(to=str(recipient), subject=subject, body=message)
            return

        if channel_type == NotificationChannelType.SLACK.value:
            payload = {"text": message}
            self._post_webhook(config["webhook_url"], payload)
            return

        if channel_type == NotificationChannelType.TEAMS.value:
            payload = {"text": message}
            self._post_webhook(config["webhook_url"], payload)
            return

        if channel_type == NotificationChannelType.WEBHOOK.value:
            payload = {"message": message, "source": settings.APP_NAME}
            headers = config.get("headers") or {}
            self._post_webhook(config["url"], payload, headers=headers)
            return

        raise ValidationAppError(f"Unsupported channel type: {channel_type}")

    def _post_webhook(
        self, url: str, payload: dict[str, Any], headers: Optional[dict[str, str]] = None
    ) -> None:
        if settings.APP_ENV == "test":
            logger.info("WEBHOOK_STUB url=%s payload=%s", url, json.dumps(payload))
            return
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload, headers=headers or {})
            response.raise_for_status()

    def _record_log(
        self,
        *,
        organization_id: int,
        channel: NotificationChannel,
        status: str,
        message: str,
        alert_id: Optional[int] = None,
        incident_id: Optional[int] = None,
        error: Optional[str] = None,
    ) -> NotificationLog:
        log = NotificationLog(
            organization_id=organization_id,
            channel_id=channel.id,
            alert_id=alert_id,
            incident_id=incident_id,
            status=status,
            message=message,
            error=error,
        )
        self.logs.add(log)
        return log

    def _format_alert_message(self, alert: Alert, asset_hostname: Optional[str]) -> str:
        host = asset_hostname or (alert.asset.hostname if alert.asset else "unknown")
        value = alert.details.get("metric_value")
        value_part = f" value={value}" if value is not None else ""
        return (
            f"[{alert.level.upper()}] {alert.alert_type} on {host}{value_part}\n"
            f"Alert ID: {alert.id} | Status: {alert.status}"
        )
