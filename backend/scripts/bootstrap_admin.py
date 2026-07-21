"""Create the first admin user on a fresh deployment when bootstrap env vars are set."""

from __future__ import annotations

import sys

from sqlalchemy import func, select

from app.core.config import settings
from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.enums import RoleName, SubscriptionPlan
from app.models.organization import Organization
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.role import RoleRepository
from app.services.alert_rule import AlertRuleService
from app.services.role import ensure_system_roles
from app.utils.slug import slugify


def main() -> int:
    email = settings.BOOTSTRAP_ADMIN_EMAIL.strip().lower()
    password = settings.BOOTSTRAP_ADMIN_PASSWORD
    if not email or not password:
        return 0

    db = SessionLocal()
    try:
        ensure_system_roles(db)
        user_count = db.scalar(select(func.count()).select_from(User)) or 0
        if user_count > 0:
            print("Bootstrap skipped: users already exist")
            return 0

        org_name = settings.BOOTSTRAP_ORG_NAME.strip() or "AIOps Organization"
        slug = slugify(org_name)
        org = Organization(
            name=org_name,
            slug=slug,
            subscription_plan=SubscriptionPlan.FREE.value,
        )
        db.add(org)
        db.flush()

        user = User(
            first_name=settings.BOOTSTRAP_ADMIN_FIRST_NAME.strip() or "Admin",
            last_name=settings.BOOTSTRAP_ADMIN_LAST_NAME.strip() or "User",
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
            is_email_verified=True,
            default_organization_id=org.id,
        )
        db.add(user)
        db.flush()

        admin_role = RoleRepository(db).get_by_name(RoleName.ORGANIZATION_ADMIN.value)
        if admin_role is None:
            print("Bootstrap failed: organization_admin role missing", file=sys.stderr)
            return 1

        db.add(
            UserRole(
                user_id=user.id,
                organization_id=org.id,
                role_id=admin_role.id,
            )
        )
        AlertRuleService(db).seed_default_rules(org.id)
        db.commit()
        print(f"Bootstrap admin created: {email}")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Bootstrap failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
