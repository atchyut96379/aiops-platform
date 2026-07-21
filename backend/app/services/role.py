from typing import Sequence

from sqlalchemy.orm import Session

from app.models.enums import ROLE_DESCRIPTIONS, RoleName
from app.models.role import Role
from app.repositories.role import RoleRepository


class RoleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.roles = RoleRepository(db)

    def list_roles(self) -> Sequence[Role]:
        return self.roles.list_all()

    def seed_system_roles(self) -> None:
        for role_name, description in ROLE_DESCRIPTIONS.items():
            existing = self.roles.get_by_name(role_name.value)
            if existing is None:
                self.roles.add(
                    Role(
                        name=role_name.value,
                        description=description,
                        is_system=True,
                    )
                )
        self.db.commit()


def ensure_system_roles(db: Session) -> None:
    RoleService(db).seed_system_roles()
