# Module 02 — Organization & Role Management

## Status

**Complete** (backend API)

## Scope

Extend multi-tenant organization management beyond Module 01 foundation:

- List and create organizations
- Organization member listing with roles
- Assign / update member roles
- Remove members
- Email-based organization invites (accept flow for new and existing users)
- Switch active organization (re-issue JWT)
- Teams and team membership
- Projects linked to teams

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/organizations` | List organizations for current user |
| POST | `/api/v1/organizations` | Create a new organization |
| GET | `/api/v1/organizations/me/members` | List members with roles (admin) |
| PATCH | `/api/v1/organizations/me/members/{user_id}/roles` | Update member roles (admin) |
| DELETE | `/api/v1/organizations/me/members/{user_id}` | Remove member (admin) |
| POST | `/api/v1/organizations/me/invites` | Invite user by email (admin) |
| GET | `/api/v1/organizations/me/invites` | List pending invites (admin) |
| DELETE | `/api/v1/organizations/me/invites/{id}` | Revoke invite (admin) |
| POST | `/api/v1/auth/accept-invite` | Accept invite (public) |
| POST | `/api/v1/users/me/switch-organization` | Switch org context + tokens |
| GET/POST/PATCH/DELETE | `/api/v1/organizations/me/teams` | Team CRUD |
| GET/POST/DELETE | `/api/v1/organizations/me/teams/{id}/members` | Team membership |
| GET/POST/PATCH/DELETE | `/api/v1/organizations/me/projects` | Project CRUD |

## Out of Scope (later modules)

- Super Admin platform-wide org management UI
- Custom (non-system) roles
- Fine-grained permission matrix
- Real SMTP delivery (email stub)
