from __future__ import annotations

import pyotp
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError, ValidationAppError
from app.models.user import User
from app.core.security import verify_password
from app.repositories.user import UserRepository


class TotpService:
    ISSUER = "AIOps Platform"

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def status(self, user: User) -> dict:
        return {"totp_enabled": bool(user.totp_enabled)}

    def setup(self, user: User) -> dict:
        if user.totp_enabled:
            raise ValidationAppError("Two-factor authentication is already enabled")

        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.totp_enabled = False
        self.db.commit()

        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name=self.ISSUER)
        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "totp_enabled": False,
        }

    def enable(self, user: User, *, code: str) -> dict:
        if not user.totp_secret:
            raise ValidationAppError("Run TOTP setup first")
        if user.totp_enabled:
            raise ValidationAppError("Two-factor authentication is already enabled")

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            raise UnauthorizedError("Invalid verification code", code="invalid_totp")

        user.totp_enabled = True
        self.db.commit()
        return {"totp_enabled": True, "message": "Two-factor authentication enabled"}

    def disable(self, user: User, *, password: str, code: str) -> dict:
        if not user.totp_enabled or not user.totp_secret:
            raise ValidationAppError("Two-factor authentication is not enabled")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid password", code="invalid_credentials")

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            raise UnauthorizedError("Invalid verification code", code="invalid_totp")

        user.totp_enabled = False
        user.totp_secret = None
        self.db.commit()
        return {"totp_enabled": False, "message": "Two-factor authentication disabled"}

    def verify_login_code(self, user: User, code: str) -> None:
        if not user.totp_enabled or not user.totp_secret:
            return
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            raise UnauthorizedError("Invalid verification code", code="invalid_totp")
