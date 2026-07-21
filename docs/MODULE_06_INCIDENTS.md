# Module 06 — Incident Management (extended)

## Status

**Partial — core + comments complete** (attachments pending)

## Scope

- Incident CRUD and lifecycle updates (open → assigned → investigating → resolved → closed)
- Auto-incident creation from critical monitoring alerts
- Incident comments timeline
- High/critical incident notifications

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/organizations/me/incidents` | Create incident |
| GET | `/api/v1/organizations/me/incidents` | List incidents |
| GET | `/api/v1/organizations/me/incidents/{id}` | Get incident |
| PATCH | `/api/v1/organizations/me/incidents/{id}` | Update incident |
| GET | `/api/v1/organizations/me/incidents/{id}/comments` | List comments |
| POST | `/api/v1/organizations/me/incidents/{id}/comments` | Add comment |

## Out of Scope (later)

- File attachments
- Full SLA tracking
- Incident ↔ alert many-to-many linking UI
