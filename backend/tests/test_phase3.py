from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "phase3@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Phase",
            "last_name": "Three",
            "email": email,
            "password": "SecurePass1",
            "organization_name": f"Phase3 Org {email}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_live_monitoring_snapshot(client: TestClient) -> None:
    data = _register(client, email="live@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/organizations/me/monitoring/live", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "as_of" in body
    assert "assets" in body


def test_knowledge_rag_indexing(client: TestClient) -> None:
    data = _register(client, email="rag@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/organizations/me/ai/knowledge",
        headers=headers,
        json={
            "title": "DB timeout runbook",
            "category": "runbook",
            "content": "When database connection timeout occurs, check connection pool settings and restart the service.",
        },
    )
    assert create.status_code == 200, create.text
    doc_id = create.json()["id"]

    reindex = client.post(
        f"/api/v1/organizations/me/ai/knowledge/{doc_id}/reindex",
        headers=headers,
    )
    assert reindex.status_code == 200


def test_cloud_integration_sync(client: TestClient) -> None:
    data = _register(client, email="cloud@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/organizations/me/integrations",
        headers=headers,
        json={
            "provider": "aws",
            "name": "Production AWS",
            "credentials": {"access_key_id": "AKIA...", "secret_access_key": "secret"},
        },
    )
    assert create.status_code == 201, create.text
    integration_id = create.json()["id"]

    sync = client.post(
        f"/api/v1/organizations/me/integrations/{integration_id}/sync",
        headers=headers,
    )
    assert sync.status_code == 200
    body = sync.json()
    assert body["assets_discovered"] >= 1
    assert body["provider"] == "aws"


def test_log_retention_job(client: TestClient) -> None:
    from app.tasks.retention import run_log_retention

    data = _register(client, email="retention@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    old_time = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    ingest = client.post(
        "/api/v1/organizations/me/logs",
        headers=headers,
        json={
            "logs": [
                {
                    "level": "info",
                    "message": "Old log entry for retention test",
                    "source": "test",
                    "logged_at": old_time,
                }
            ]
        },
    )
    assert ingest.status_code == 201

    result = run_log_retention()
    assert result["organizations_processed"] >= 1
