from datetime import datetime, timezone

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "admin@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": email,
            "password": "SecurePass1",
            "organization_name": f"Acme {email}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_incident_crud_workflow(client: TestClient) -> None:
    data = _register(client, email="incident@example.com")
    token = data["tokens"]["access_token"]

    project_resp = client.post(
        "/api/v1/organizations/me/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Ops Project", "description": "Incident test project"},
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    asset_resp = client.post(
        "/api/v1/organizations/me/assets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_type": "linux_server",
            "hostname": "incident-server.example.com",
            "ip_address": "10.0.0.5",
            "os": "Ubuntu 24.04",
            "environment": "production",
            "project_id": project_id,
            "status": "healthy",
            "tags": ["incident", "prod"],
            "metadata": {"region": "us-east-1"},
        },
    )
    assert asset_resp.status_code == 201
    asset_id = asset_resp.json()["id"]

    create_resp = client.post(
        "/api/v1/organizations/me/incidents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_id": asset_id,
            "incident_type": "performance",
            "title": "High CPU alert",
            "description": "CPU has sustained values above 90%",
            "severity": "critical",
            "details": {"cpu": 95.3, "duration_minutes": 12},
        },
    )
    assert create_resp.status_code == 201
    incident = create_resp.json()
    incident_id = incident["id"]
    assert incident["status"] == "open"
    assert incident["incident_type"] == "performance"

    list_resp = client.get(
        "/api/v1/organizations/me/incidents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert any(item["id"] == incident_id for item in list_resp.json())

    get_resp = client.get(
        f"/api/v1/organizations/me/incidents/{incident_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "High CPU alert"

    update_resp = client.patch(
        f"/api/v1/organizations/me/incidents/{incident_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "in_progress", "assignee_user_id": data["user"]["id"], "resolution": "Investigating suspect process"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "in_progress"
    assert update_resp.json()["resolution"] == "Investigating suspect process"
