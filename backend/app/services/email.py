import smtplib
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Send email via SMTP when configured; otherwise log a stub message."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        if not settings.EMAIL_ENABLED:
            logger.info("EMAIL_STUB to=%s subject=%s body=%s", to, subject, body)
            return

        if not settings.smtp_configured:
            logger.warning(
                "EMAIL_ENABLED=true but SMTP_HOST is not set; logging message instead"
            )
            logger.info("EMAIL to=%s subject=%s body=%s", to, subject, body)
            return

        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = settings.EMAIL_FROM
        message["To"] = to

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
            logger.info("EMAIL_SENT to=%s subject=%s", to, subject)
        except Exception:
            logger.exception("Failed to send email to %s", to)
            raise

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
