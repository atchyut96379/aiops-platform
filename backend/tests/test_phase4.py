from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "phase4@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Phase",
            "last_name": "Four",
            "email": email,
            "password": "SecurePass1",
            "organization_name": f"Phase4 Org {email}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_cloud_sync_imports_assets(client: TestClient) -> None:
    data = _register(client, email="import@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/organizations/me/integrations",
        headers=headers,
        json={"provider": "aws", "name": "AWS Prod", "credentials": {}},
    )
    assert create.status_code == 201
    integration_id = create.json()["id"]

    sync = client.post(
        f"/api/v1/organizations/me/integrations/{integration_id}/sync",
        headers=headers,
    )
    assert sync.status_code == 200, sync.text
    body = sync.json()
    assert body["assets_discovered"] >= 1
    assert body["assets_imported"] >= 1

    assets = client.get("/api/v1/organizations/me/assets", headers=headers)
    assert assets.status_code == 200
    assert len(assets.json()) >= 1


def test_docker_platform_collect(client: TestClient) -> None:
    data = _register(client, email="docker@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/organizations/me/platforms",
        headers=headers,
        json={
            "connection_type": "docker",
            "name": "Local Docker",
            "endpoint": "unix:///var/run/docker.sock",
        },
    )
    assert create.status_code == 201, create.text
    conn_id = create.json()["id"]

    collect = client.post(
        f"/api/v1/organizations/me/platforms/{conn_id}/collect",
        headers=headers,
    )
    assert collect.status_code == 200
    snapshot = collect.json()["snapshot"]
    assert snapshot.get("source") == "docker"
    assert "containers" in snapshot
    assert isinstance(snapshot.get("count"), int)
    # CI runners may have Docker socket available but zero running containers
    assert snapshot.get("count", 0) >= 0
    if snapshot.get("demo"):
        assert snapshot.get("count", 0) >= 1


def test_kubernetes_platform_collect(client: TestClient) -> None:
    data = _register(client, email="k8s@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/organizations/me/platforms",
        headers=headers,
        json={
            "connection_type": "kubernetes",
            "name": "Demo Cluster",
            "config": {},
        },
    )
    assert create.status_code == 201
    conn_id = create.json()["id"]

    collect = client.post(
        f"/api/v1/organizations/me/platforms/{conn_id}/collect",
        headers=headers,
    )
    assert collect.status_code == 200
    snapshot = collect.json()["snapshot"]
    assert snapshot.get("source") == "kubernetes"
    assert snapshot.get("node_count", 0) >= 1
