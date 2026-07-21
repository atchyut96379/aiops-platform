# Module 05 — Alerting & Notifications

## Status

**Complete** (backend API — delivery layer)

## Scope

- Organization notification channels: email, Slack, Microsoft Teams, generic webhook
- Minimum alert level per channel (critical, high, warning, medium, low)
- Automatic dispatch when alerts are created from monitoring thresholds
- Automatic dispatch for high/critical incidents
- Delivery logs for audit and troubleshooting

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/organizations/me/notification-channels` | List channels |
| POST | `/api/v1/organizations/me/notification-channels` | Create channel (admin) |
| PATCH | `/api/v1/organizations/me/notification-channels/{id}` | Update channel (admin) |
| DELETE | `/api/v1/organizations/me/notification-channels/{id}` | Deactivate channel (admin) |
| GET | `/api/v1/organizations/me/notification-logs` | List delivery logs (admin) |

## Channel config examples

**Email:** `{ "recipients": ["ops@company.com"] }`  
**Slack / Teams:** `{ "webhook_url": "https://..." }`  
**Webhook:** `{ "url": "https://...", "headers": { "Authorization": "Bearer ..." } }`

## Out of Scope (later)

- Per-user notification preferences
- SMS / PagerDuty integrations
- Retry queues and dead-letter handling
