# Module 03 — Infrastructure Inventory

## Status

**Complete** (backend API)

## Scope

Register and manage infrastructure assets per organization:

- Linux / Windows servers, VMs, AWS EC2, Azure VM, GCP VM, Kubernetes clusters, Docker hosts
- Hostname, IP, OS, environment, owner, tags, cloud metadata
- Optional project association
- Inventory stats by type and status

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/organizations/me/assets` | List assets (filter/search) |
| POST | `/api/v1/organizations/me/assets` | Register asset |
| GET | `/api/v1/organizations/me/assets/stats` | Inventory summary |
| GET | `/api/v1/organizations/me/assets/{id}` | Get asset |
| PATCH | `/api/v1/organizations/me/assets/{id}` | Update asset |
| DELETE | `/api/v1/organizations/me/assets/{id}` | Soft-delete asset |

## RBAC

- **Read**: all authenticated org members (including read_only)
- **Write**: organization_admin, devops_engineer, cloud_engineer, super_admin

## Out of Scope (Module 04+)

- Live monitoring metrics ingestion
- Heartbeat / health check agents
- Threshold alerts
