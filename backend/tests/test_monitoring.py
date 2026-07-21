from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.models.infrastructure_asset import InfrastructureAsset
from app.models.project import Project
from app.models.team import Team
from app.services.user import UserService


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


def test_monitoring_asset_metrics(client: TestClient) -> None:
    data = _register(client, email="monitor@example.com")
    token = data["tokens"]["access_token"]

    # Create project and asset for the organization
    project_resp = client.post(
        "/api/v1/organizations/me/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Infra Project", "description": "Test project"},
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    asset_resp = client.post(
        "/api/v1/organizations/me/assets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_type": "linux_server",
            "hostname": "test-server.example.com",
            "ip_address": "10.0.0.1",
            "os": "Ubuntu 24.04",
            "environment": "production",
            "project_id": project_id,
            "status": "healthy",
            "tags": ["web", "prod"],
            "metadata": {"region": "us-east-1"},
        },
    )
    assert asset_resp.status_code == 201
    asset_id = asset_resp.json()["id"]

    metric_resp = client.post(
        f"/api/v1/organizations/me/monitoring/assets/{asset_id}/metrics",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "metric_type": "cpu.percent",
            "metric_value": 32.5,
            "unit": "%",
            "details": {"core_count": 8},
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert metric_resp.status_code == 201
    metric_body = metric_resp.json()
    assert metric_body["asset_id"] == asset_id
    assert metric_body["metric_type"] == "cpu.percent"
    assert metric_body["metric_value"] == 32.5

    list_resp = client.get(
        f"/api/v1/organizations/me/monitoring/assets/{asset_id}/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    health_resp = client.get(
        f"/api/v1/organizations/me/monitoring/assets/{asset_id}/health",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] in {"healthy", "warning", "critical"}

    stats_resp = client.get(
        f"/api/v1/organizations/me/monitoring/assets/{asset_id}/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stats_resp.status_code == 200
    assert stats_resp.json()["count_by_type"]["cpu.percent"] == 1
