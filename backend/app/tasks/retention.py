from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.log_entry import LogEntry
from app.models.organization import Organization
from app.services.subscription import get_plan_limits

logger = get_logger(__name__)


def run_log_retention() -> dict[str, int]:
    """Delete log entries older than each organization's plan retention window."""
    db = SessionLocal()
    deleted_total = 0
    orgs_processed = 0
    try:
        organizations = db.scalars(select(Organization)).all()
        now = datetime.now(timezone.utc)
        for org in organizations:
            limits = get_plan_limits(org.subscription_plan)
            cutoff = now - timedelta(days=limits.log_retention_days)
            result = db.execute(
                delete(LogEntry).where(
                    LogEntry.organization_id == org.id,
                    LogEntry.logged_at < cutoff,
                )
            )
            deleted = result.rowcount or 0
            if deleted:
                logger.info(
                    "Retention: deleted %s log entries for org %s (plan=%s)",
                    deleted,
                    org.id,
                    org.subscription_plan,
                )
            deleted_total += deleted
            orgs_processed += 1
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Log retention job failed")
        raise
    finally:
        db.close()
    return {"organizations_processed": orgs_processed, "entries_deleted": deleted_total}
