# Module 01 — Authentication & User Management

## Status

**Complete** (backend API)

## Scope

Implement secure multi-tenant authentication and user lifecycle APIs:

- User registration (creates personal org or joins by invite later)
- Login / logout with JWT access + refresh tokens
- Password change, password reset (token-based)
- Email verification (token-based)
- User profile read/update
- Role definitions and assignment foundation
- Organization foundation (required for multi-tenant JWT claims)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register user + default organization |
| POST | `/api/v1/auth/login` | Obtain access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Rotate tokens |
| POST | `/api/v1/auth/logout` | Revoke refresh token |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password with token |
| POST | `/api/v1/auth/verify-email` | Verify email with token |
| POST | `/api/v1/auth/resend-verification` | Resend verification email |
| POST | `/api/v1/auth/change-password` | Change password (authenticated) |
| GET | `/api/v1/users/me` | Current user profile |
| PATCH | `/api/v1/users/me` | Update profile |
| GET | `/api/v1/users` | List users in current org (admin) |
| GET | `/api/v1/organizations/me` | Current organization |
| PATCH | `/api/v1/organizations/me` | Update organization (admin) |
| GET | `/api/v1/roles` | List available roles |

## Security

- Bcrypt password hashing
- Short-lived JWT access tokens
- Longer-lived refresh tokens stored hashed in DB (revocable)
- RBAC dependency guards
- CORS, rate limiting on auth endpoints
- Pydantic input validation

## Out of Scope (later modules)

- Full invite flow, teams, projects
- Audit log persistence (stub hooks only)
- Frontend UI
- Real SMTP delivery (console/log stub in Module 01)
