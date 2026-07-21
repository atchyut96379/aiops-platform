from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """SMTP stub for Module 01. Logs messages when EMAIL_ENABLED is false."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        if not settings.EMAIL_ENABLED:
            logger.info(
                "EMAIL_STUB to=%s subject=%s body=%s",
                to,
                subject,
                body,
            )
            return
        # Real SMTP integration deferred to a later module / ops config.
        logger.warning("EMAIL_ENABLED=true but SMTP transport is not configured; logging instead")
        logger.info("EMAIL to=%s subject=%s body=%s", to, subject, body)

    def send_verification(self, *, to: str, token: str) -> None:
        link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        self.send(
            to=to,
            subject=f"{settings.APP_NAME} — Verify your email",
            body=f"Verify your email by opening: {link}",
        )

    def send_password_reset(self, *, to: str, token: str) -> None:
        link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        self.send(
            to=to,
            subject=f"{settings.APP_NAME} — Reset your password",
            body=f"Reset your password by opening: {link}",
        )

    def send_organization_invite(
        self, *, to: str, token: str, organization_name: str
    ) -> None:
        link = f"{settings.FRONTEND_URL}/accept-invite?token={token}"
        self.send(
            to=to,
            subject=f"{settings.APP_NAME} — Invitation to join {organization_name}",
            body=f"You have been invited to join {organization_name}. Accept the invite: {link}",
        )
