from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    User,
)
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower())
        return self.db.scalar(stmt)

    def list_by_organization(
        self, organization_id: int, *, skip: int = 0, limit: int = 50
    ) -> Sequence[User]:
        from app.models.user_role import UserRole

        stmt = (
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .where(UserRole.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .distinct()
        )
        return self.db.scalars(stmt).all()

    def update_last_login(self, user: User) -> User:
        user.last_login_at = datetime.now(timezone.utc)
        self.db.flush()
        self.db.refresh(user)
        return user


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RefreshToken)

    def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        return self.db.scalar(stmt)

    def revoke(self, token: RefreshToken) -> None:
        token.revoked = True
        self.db.flush()

    def revoke_all_for_user(self, user_id: int) -> None:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
        )
        for token in self.db.scalars(stmt).all():
            token.revoked = True
        self.db.flush()


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PasswordResetToken)

    def get_valid_by_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        now = datetime.now(timezone.utc)
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > now,
        )
        return self.db.scalar(stmt)


class EmailVerificationTokenRepository(BaseRepository[EmailVerificationToken]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, EmailVerificationToken)

    def get_valid_by_hash(self, token_hash: str) -> Optional[EmailVerificationToken]:
        now = datetime.now(timezone.utc)
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used.is_(False),
            EmailVerificationToken.expires_at > now,
        )
        return self.db.scalar(stmt)
