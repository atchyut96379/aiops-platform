from datetime import datetime, timezone

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "notify@example.com") -> dict:
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


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_notification_channel_and_alert_delivery(client: TestClient) -> None:
    data = _register(client, email="notify@example.com")
    token = data["tokens"]["access_token"]
    headers = _auth(token)

    channel_resp = client.post(
        "/api/v1/organizations/me/notification-channels",
        headers=headers,
        json={
            "name": "Ops Email",
            "channel_type": "email",
            "config": {"recipients": ["ops@example.com"]},
            "min_alert_level": "warning",
        },
    )
    assert channel_resp.status_code == 201, channel_resp.text

    asset_resp = client.post(
        "/api/v1/organizations/me/assets",
        headers=headers,
        json={
            "asset_type": "linux_server",
            "hostname": "notify-server.example.com",
            "environment": "production",
        },
    )
    assert asset_resp.status_code == 201
    asset_id = asset_resp.json()["id"]

    metric_resp = client.post(
        f"/api/v1/organizations/me/monitoring/assets/{asset_id}/metrics",
        headers=headers,
        json={
            "metric_type": "cpu.percent",
            "metric_value": 95.0,
            "unit": "%",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert metric_resp.status_code == 201

    logs_resp = client.get("/api/v1/organizations/me/notification-logs", headers=headers)
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) >= 1
    assert any(log["status"] == "sent" for log in logs)


def test_incident_comments(client: TestClient) -> None:
    data = _register(client, email="comments@example.com")
    token = data["tokens"]["access_token"]
    headers = _auth(token)

    incident_resp = client.post(
        "/api/v1/organizations/me/incidents",
        headers=headers,
        json={
            "incident_type": "manual",
            "title": "Database latency spike",
            "description": "Users reporting slow queries",
            "severity": "high",
        },
    )
    assert incident_resp.status_code == 201, incident_resp.text
    incident_id = incident_resp.json()["id"]

    comment_resp = client.post(
        f"/api/v1/organizations/me/incidents/{incident_id}/comments",
        headers=headers,
        json={"body": "Checking slow query log on primary DB."},
    )
    assert comment_resp.status_code == 201
    assert comment_resp.json()["body"].startswith("Checking slow query")

    list_resp = client.get(
        f"/api/v1/organizations/me/incidents/{incident_id}/comments",
        headers=headers,
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    detail_resp = client.get(
        f"/api/v1/organizations/me/incidents/{incident_id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["comment_count"] == 1
