from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user_role import UserRole
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Role)

    def get_by_name(self, name: str) -> Optional[Role]:
        stmt = select(Role).where(Role.name == name)
        return self.db.scalar(stmt)

    def list_all(self) -> Sequence[Role]:
        return self.db.scalars(select(Role).order_by(Role.name)).all()


class UserRoleRepository(BaseRepository[UserRole]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, UserRole)

    def list_for_user(self, user_id: int) -> Sequence[UserRole]:
        stmt = select(UserRole).where(UserRole.user_id == user_id)
        return self.db.scalars(stmt).all()

    def list_for_user_org(self, user_id: int, organization_id: int) -> Sequence[UserRole]:
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.organization_id == organization_id,
        )
        return self.db.scalars(stmt).all()

    def exists(self, user_id: int, organization_id: int, role_id: int) -> bool:
        stmt = select(UserRole.id).where(
            UserRole.user_id == user_id,
            UserRole.organization_id == organization_id,
            UserRole.role_id == role_id,
        )
        return self.db.scalar(stmt) is not None
