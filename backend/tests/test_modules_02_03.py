from fastapi.testclient import TestClient

from app.core.security import hash_opaque_token
from app.models.organization_invite import OrganizationInvite
from app.utils.tokens import generate_url_safe_token


def _register(client: TestClient, email: str = "admin@example.com", org_name: str | None = None) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": email,
            "password": "SecurePass1",
            "organization_name": org_name or f"Acme {email}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_list_and_create_organization(client: TestClient) -> None:
    data = _register(client, email="orglist@example.com")
    token = data["tokens"]["access_token"]

    listed = client.get("/api/v1/organizations", headers=_auth_headers(token))
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    created = client.post(
        "/api/v1/organizations",
        headers=_auth_headers(token),
        json={"name": "Second Org"},
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Second Org"

    listed_after = client.get("/api/v1/organizations", headers=_auth_headers(token))
    assert len(listed_after.json()) == 2


def test_create_team_and_project(client: TestClient) -> None:
    data = _register(client, email="teamproj@example.com")
    token = data["tokens"]["access_token"]
    headers = _auth_headers(token)

    team = client.post(
        "/api/v1/organizations/me/teams",
        headers=headers,
        json={"name": "Platform Team", "description": "Core platform"},
    )
    assert team.status_code == 201
    team_id = team.json()["id"]

    project = client.post(
        "/api/v1/organizations/me/projects",
        headers=headers,
        json={"name": "Core Services", "team_id": team_id, "environment": "production"},
    )
    assert project.status_code == 201
    assert project.json()["team_id"] == team_id

    teams = client.get("/api/v1/organizations/me/teams", headers=headers)
    assert teams.status_code == 200
    assert len(teams.json()) == 1


def test_invite_and_accept_new_user(client: TestClient, db) -> None:
    admin = _register(client, email="inviter@example.com")
    token = admin["tokens"]["access_token"]
    headers = _auth_headers(token)

    invite_resp = client.post(
        "/api/v1/organizations/me/invites",
        headers=headers,
        json={"email": "invited@example.com", "role": "devops_engineer"},
    )
    assert invite_resp.status_code == 201
    invite_id = invite_resp.json()["id"]

    raw_token = generate_url_safe_token()
    invite = db.get(OrganizationInvite, invite_id)
    assert invite is not None
    invite.token_hash = hash_opaque_token(raw_token)
    db.commit()

    accepted = client.post(
        "/api/v1/auth/accept-invite",
        json={
            "token": raw_token,
            "first_name": "Grace",
            "last_name": "Hopper",
            "password": "SecurePass1",
        },
    )
    assert accepted.status_code == 200, accepted.text
    body = accepted.json()
    assert body["user"]["email"] == "invited@example.com"
    assert body["tokens"]["access_token"]

    members = client.get("/api/v1/organizations/me/members", headers=headers)
    assert members.status_code == 200
    emails = {m["user"]["email"] for m in members.json()}
    assert "invited@example.com" in emails


def test_infrastructure_asset_crud(client: TestClient) -> None:
    data = _register(client, email="infra@example.com")
    token = data["tokens"]["access_token"]
    headers = _auth_headers(token)

    created = client.post(
        "/api/v1/organizations/me/assets",
        headers=headers,
        json={
            "asset_type": "linux_server",
            "hostname": "web-01.prod.local",
            "ip_address": "10.0.0.10",
            "os": "Ubuntu 22.04",
            "environment": "production",
            "tags": ["web", "nginx"],
            "metadata": {"region": "us-east-1"},
        },
    )
    assert created.status_code == 201, created.text
    asset_id = created.json()["id"]

    listed = client.get("/api/v1/organizations/me/assets", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    stats = client.get("/api/v1/organizations/me/assets/stats", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["total"] == 1
    assert stats.json()["by_type"]["linux_server"] == 1

    updated = client.patch(
        f"/api/v1/organizations/me/assets/{asset_id}",
        headers=headers,
        json={"status": "healthy"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "healthy"

    deleted = client.delete(f"/api/v1/organizations/me/assets/{asset_id}", headers=headers)
    assert deleted.status_code == 204

    listed_after = client.get("/api/v1/organizations/me/assets", headers=headers)
    assert listed_after.json() == []
