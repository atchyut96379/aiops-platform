from datetime import datetime, timezone

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "alert@example.com") -> dict:
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


def test_alert_created_from_metric(client: TestClient) -> None:
    data = _register(client, email="alert@example.com")
    token = data["tokens"]["access_token"]

    project_resp = client.post(
        "/api/v1/organizations/me/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Alert Project", "description": "Alert test project"},
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    asset_resp = client.post(
        "/api/v1/organizations/me/assets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_type": "linux_server",
            "hostname": "alert-server.example.com",
            "ip_address": "10.0.0.9",
            "os": "Ubuntu 24.04",
            "environment": "production",
            "project_id": project_id,
            "status": "healthy",
            "tags": ["alert", "prod"],
            "metadata": {"region": "us-east-1"},
        },
    )
    assert asset_resp.status_code == 201
    asset_id = asset_resp.json()["id"]

    # send a critical cpu metric
    metric_resp = client.post(
        f"/api/v1/organizations/me/monitoring/assets/{asset_id}/metrics",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "metric_type": "cpu.percent",
            "metric_value": 95.0,
            "unit": "%",
            "details": {"core_count": 8},
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert metric_resp.status_code == 201

    # alerts should be present via list API
    alerts_resp = client.get(
        "/api/v1/organizations/me/alerts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert any(a["alert_type"] == "cpu.percent" and a["level"] == "critical" for a in alerts)


def test_acknowledge_and_resolve_alert_via_api(client: TestClient) -> None:
    data = _register(client, email="ack@example.com")
    token = data["tokens"]["access_token"]

    project_resp = client.post(
        "/api/v1/organizations/me/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Ack Project", "description": "Ack test project"},
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    asset_resp = client.post(
        "/api/v1/organizations/me/assets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_type": "linux_server",
            "hostname": "ack-server.example.com",
            "ip_address": "10.0.0.10",
            "os": "Ubuntu 24.04",
            "environment": "production",
            "project_id": project_id,
            "status": "healthy",
            "tags": ["ack", "prod"],
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
            "metric_value": 92.0,
            "unit": "%",
            "details": {},
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert metric_resp.status_code == 201

    alerts_resp = client.get(
        "/api/v1/organizations/me/alerts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    critical = next((a for a in alerts if a["alert_type"] == "cpu.percent" and a["level"] == "critical"), None)
    assert critical is not None
    alert_id = critical["id"]

    # Acknowledge
    ack_resp = client.post(
        f"/api/v1/organizations/me/alerts/{alert_id}/acknowledge",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ack_resp.status_code == 200, ack_resp.text
    ack = ack_resp.json()
    assert ack["acknowledged"] is True
    assert ack["acknowledged_by_id"] is not None

    # Resolve
    res_resp = client.post(
        f"/api/v1/organizations/me/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_resp.status_code == 200, res_resp.text
    resolved = res_resp.json()
    assert resolved["resolved"] is True
    assert resolved["status"] == "resolved"
