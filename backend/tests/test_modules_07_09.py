import io

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "mod7@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Grace",
            "last_name": "Hopper",
            "email": email,
            "password": "SecurePass1",
            "organization_name": f"Org {email}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_dashboard_summary_and_trends(client: TestClient) -> None:
    data = _register(client, email="dash@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    summary = client.get("/api/v1/organizations/me/dashboard", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert "total_assets" in body
    assert "open_alerts" in body

    trends = client.get("/api/v1/organizations/me/dashboard/trends?days=7", headers=headers)
    assert trends.status_code == 200
    assert trends.json()["days"] == 7


def test_audit_logs_list_and_export(client: TestClient) -> None:
    data = _register(client, email="audit@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logs = client.get("/api/v1/organizations/me/audit-logs", headers=headers)
    assert logs.status_code == 200
    assert isinstance(logs.json(), list)
    assert len(logs.json()) >= 1

    export = client.get("/api/v1/organizations/me/audit-logs/export", headers=headers)
    assert export.status_code == 200
    assert "id,action" in export.text


def test_ai_and_knowledge_base(client: TestClient) -> None:
    data = _register(client, email="ai@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    doc = client.post(
        "/api/v1/organizations/me/ai/knowledge",
        headers=headers,
        json={
            "title": "Restart nginx",
            "category": "runbook",
            "content": "Run systemctl restart nginx on affected hosts.",
            "tags": "nginx,linux",
        },
    )
    assert doc.status_code == 200
    assert doc.json()["title"] == "Restart nginx"

    docs = client.get("/api/v1/organizations/me/ai/knowledge", headers=headers)
    assert docs.status_code == 200
    assert any(d["title"] == "Restart nginx" for d in docs.json())

    analysis = client.post(
        "/api/v1/organizations/me/ai/analyze-logs",
        headers=headers,
        json={"log_text": "ERROR nginx connection refused on port 443"},
    )
    assert analysis.status_code == 200
    assert analysis.json()["summary"]

    chat = client.post(
        "/api/v1/organizations/me/ai/chat",
        headers=headers,
        json={"message": "How do I restart nginx?"},
    )
    assert chat.status_code == 200
    assert chat.json()["reply"]


def test_incident_attachments(client: TestClient) -> None:
    data = _register(client, email="attach@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    incident_resp = client.post(
        "/api/v1/organizations/me/incidents",
        headers=headers,
        json={
            "incident_type": "outage",
            "title": "Attachment test",
            "description": "Testing file upload",
            "severity": "medium",
        },
    )
    assert incident_resp.status_code == 201
    incident_id = incident_resp.json()["id"]

    upload = client.post(
        f"/api/v1/organizations/me/incidents/{incident_id}/attachments",
        headers=headers,
        files={"file": ("notes.txt", io.BytesIO(b"incident notes"), "text/plain")},
    )
    assert upload.status_code == 201
    attachment_id = upload.json()["id"]

    listed = client.get(
        f"/api/v1/organizations/me/incidents/{incident_id}/attachments",
        headers=headers,
    )
    assert listed.status_code == 200
    assert any(a["id"] == attachment_id for a in listed.json())

    download = client.get(
        f"/api/v1/organizations/me/incidents/{incident_id}/attachments/{attachment_id}/download",
        headers=headers,
    )
    assert download.status_code == 200
    assert download.content == b"incident notes"
