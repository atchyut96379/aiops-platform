from typing import Sequence

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import User
from app.repositories.role import UserRoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserProfileResponse, UserResponse, UserRoleInfo, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.memberships = UserRoleRepository(db)

    def get_profile(self, user: User) -> UserProfileResponse:
        memberships = self.memberships.list_for_user(user.id)
        membership_info = [
            UserRoleInfo(
                organization_id=m.organization_id,
                organization_name=m.organization.name if m.organization else "",
                role_name=m.role.name if m.role else "",
            )
            for m in memberships
        ]
        base = UserResponse.model_validate(user)
        return UserProfileResponse(**base.model_dump(), memberships=membership_info)

    def update_profile(self, user: User, payload: UserUpdate) -> User:
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_organization_users(
        self,
        *,
        organization_id: int,
        requester: User,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[User]:
        if not requester.is_superuser:
            memberships = self.memberships.list_for_user_org(requester.id, organization_id)
            if not memberships:
                raise ForbiddenError("Not a member of this organization")
        return self.users.list_by_organization(organization_id, skip=skip, limit=limit)

    def get_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user
