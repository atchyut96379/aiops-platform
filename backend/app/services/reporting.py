from datetime import datetime
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, ValidationAppError
from app.models.incident import Incident
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.role import UserRoleRepository
from app.services.subscription import get_plan_limits


class ReportingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.memberships = UserRoleRepository(db)
        self.orgs = OrganizationRepository(db)

    def export_incidents_pdf(self, *, organization_id: int, requester: User) -> bytes:
        self._require_member(requester, organization_id)
        self._require_pdf(organization_id)
        incidents = self._fetch_incidents(organization_id)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("AIOps Platform — Incident Report", styles["Title"]),
            Spacer(1, 12),
            Paragraph(
                f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                styles["Normal"],
            ),
            Spacer(1, 12),
        ]
        data = [["ID", "Title", "Severity", "Status", "Created"]]
        for inc in incidents[:200]:
            data.append([
                str(inc.id),
                inc.title[:60],
                inc.severity,
                inc.status,
                inc.created_at.strftime("%Y-%m-%d") if inc.created_at else "",
            ])
        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1976d2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(table)
        doc.build(story)
        return buffer.getvalue()

    def export_incidents_xlsx(self, *, organization_id: int, requester: User) -> bytes:
        self._require_member(requester, organization_id)
        self._require_excel(organization_id)
        incidents = self._fetch_incidents(organization_id)
        wb = Workbook()
        ws = wb.active
        ws.title = "Incidents"
        ws.append(["ID", "Title", "Severity", "Status", "Type", "Asset ID", "Created At"])
        for inc in incidents:
            ws.append([
                inc.id,
                inc.title,
                inc.severity,
                inc.status,
                inc.incident_type,
                inc.asset_id,
                inc.created_at.isoformat() if inc.created_at else "",
            ])
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    def _fetch_incidents(self, organization_id: int) -> list[Incident]:
        return list(
            self.db.scalars(
                select(Incident)
                .where(Incident.organization_id == organization_id)
                .order_by(Incident.created_at.desc())
                .limit(5000)
            ).all()
        )

    def _require_pdf(self, organization_id: int) -> None:
        org = self.orgs.get(organization_id)
        if org is None:
            raise ValidationAppError("Organization not found")
        limits = get_plan_limits(org.subscription_plan)
        if not limits.pdf_reports:
            raise ValidationAppError(
                "PDF reports require Starter plan or above. Upgrade your subscription."
            )

    def _require_excel(self, organization_id: int) -> None:
        org = self.orgs.get(organization_id)
        if org is None:
            raise ValidationAppError("Organization not found")
        limits = get_plan_limits(org.subscription_plan)
        if not limits.excel_reports:
            raise ValidationAppError(
                "Excel reports require Starter plan or above. Upgrade your subscription."
            )

    def _require_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")
