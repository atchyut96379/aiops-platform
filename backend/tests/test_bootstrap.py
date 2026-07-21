from sqlalchemy import func, select

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.user import User
from scripts.bootstrap_admin import main


def test_bootstrap_admin_creates_first_user(monkeypatch) -> None:
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_EMAIL", "bootstrap@example.com")
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", "SecurePass1")
    monkeypatch.setattr(settings, "BOOTSTRAP_ORG_NAME", "Bootstrap Org")

    db = SessionLocal()
    try:
        before = db.scalar(select(func.count()).select_from(User)) or 0
        if before == 0:
            assert main() == 0
            after = db.scalar(select(func.count()).select_from(User)) or 0
            assert after == 1
            user = db.execute(select(User).where(User.email == "bootstrap@example.com")).scalar_one()
            assert user.is_email_verified is True
        else:
            assert main() == 0
    finally:
        db.close()
