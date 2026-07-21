from datetime import datetime, timezone

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "agent@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Agent",
            "last_name": "Tester",
            "email": email,
            "password": "SecurePass1",
            "organization_name": f"Agent Org {email}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_asset(client: TestClient, token: str) -> int:
    project_resp = client.post(
        "/api/v1/organizations/me/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Agent Project", "description": "test"},
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    asset_resp = client.post(
        "/api/v1/organizations/me/assets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_type": "linux_server",
            "hostname": "agent-server.example.com",
            "ip_address": "10.0.0.20",
            "os": "Ubuntu 24.04",
            "environment": "production",
            "project_id": project_id,
            "status": "healthy",
            "tags": [],
            "metadata": {},
        },
    )
    assert asset_resp.status_code == 201
    return asset_resp.json()["id"]


def test_create_agent_and_ingest_metrics(client: TestClient) -> None:
    data = _register(client, email="agent-ingest@example.com")
    token = data["tokens"]["access_token"]
    asset_id = _create_asset(client, token)

    agent_resp = client.post(
        "/api/v1/organizations/me/agents",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Agent", "asset_id": asset_id, "hostname": "test-host"},
    )
    assert agent_resp.status_code == 201, agent_resp.text
    agent = agent_resp.json()
    api_key = agent["api_key"]
    assert api_key.startswith("aiops_")

    headers = {"X-Agent-Key": api_key}
    heartbeat = client.post(
        "/api/v1/agent/heartbeat",
        headers=headers,
        json={"agent_version": "1.0.0", "hostname": "test-host"},
    )
    assert heartbeat.status_code == 200

    metrics = client.post(
        "/api/v1/agent/metrics",
        headers=headers,
        json={"metrics": [{"metric_type": "cpu.percent", "metric_value": 95.0, "unit": "%"}]},
    )
    assert metrics.status_code == 200
    assert metrics.json()["ingested"] == 1

    alerts_resp = client.get(
        "/api/v1/organizations/me/alerts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert any(a["level"] == "critical" for a in alerts)


def test_alert_rules_crud(client: TestClient) -> None:
    data = _register(client, email="rules@example.com")
    token = data["tokens"]["access_token"]

    list_resp = client.get(
        "/api/v1/organizations/me/alert-rules",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 4  # default seeded rules

    create_resp = client.post(
        "/api/v1/organizations/me/alert-rules",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Custom disk rule",
            "metric_type": "disk.percent",
            "operator": "gte",
            "threshold": 85,
            "level": "warning",
        },
    )
    assert create_resp.status_code == 201
    rule_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/organizations/me/alert-rules/{rule_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled": False},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["enabled"] is False


def test_log_search(client: TestClient) -> None:
    data = _register(client, email="logs@example.com")
    token = data["tokens"]["access_token"]

    ingest = client.post(
        "/api/v1/organizations/me/logs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "logs": [
                {
                    "level": "error",
                    "message": "Database connection timeout on prod-db",
                    "source": "api",
                    "logged_at": datetime.now(timezone.utc).isoformat(),
                }
            ]
        },
    )
    assert ingest.status_code == 201

    search = client.get(
        "/api/v1/organizations/me/logs?q=timeout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert search.status_code == 200
    body = search.json()
    assert body["total"] >= 1
    assert any("timeout" in item["message"].lower() for item in body["items"])
