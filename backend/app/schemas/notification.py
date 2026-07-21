from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import AlertLevel, NotificationChannelType
from app.schemas.common import ORMModel


class NotificationChannelCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    channel_type: NotificationChannelType
    config: dict[str, Any] = Field(default_factory=dict)
    min_alert_level: AlertLevel = AlertLevel.MEDIUM
    is_active: bool = True

    @model_validator(mode="after")
    def validate_channel_config(self) -> "NotificationChannelCreate":
        if self.channel_type == NotificationChannelType.EMAIL:
            recipients = self.config.get("recipients")
            if not recipients or not isinstance(recipients, list):
                raise ValueError("email config requires non-empty 'recipients' list")
        elif self.channel_type == NotificationChannelType.SLACK:
            if not self.config.get("webhook_url"):
                raise ValueError("slack config requires 'webhook_url'")
        elif self.channel_type == NotificationChannelType.TEAMS:
            if not self.config.get("webhook_url"):
                raise ValueError("teams config requires 'webhook_url'")
        elif self.channel_type == NotificationChannelType.WEBHOOK:
            if not self.config.get("url"):
                raise ValueError("webhook config requires 'url'")
        return self


class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    config: Optional[dict[str, Any]] = None
    min_alert_level: Optional[AlertLevel] = None
    is_active: Optional[bool] = None


class NotificationChannelResponse(ORMModel):
    id: int
    organization_id: int
    name: str
    channel_type: str
    config: dict[str, Any] = Field(default_factory=dict)
    min_alert_level: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NotificationLogResponse(ORMModel):
    id: int
    organization_id: int
    channel_id: Optional[int] = None
    alert_id: Optional[int] = None
    incident_id: Optional[int] = None
    status: str
    message: str
    error: Optional[str] = None
    created_at: Optional[datetime] = None
