import pyotp
from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "phase5@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Phase",
            "last_name": "Five",
            "email": email,
            "password": "SecurePass1",
            "organization_name": f"Phase5 Org {email}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_demo_billing_checkout_upgrades_plan(client: TestClient) -> None:
    data = _register(client, email="billing@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    plan = client.get("/api/v1/organizations/me/billing/plan", headers=headers)
    assert plan.status_code == 200
    assert plan.json()["plan"] == "free"

    checkout = client.post(
        "/api/v1/organizations/me/billing/checkout",
        headers=headers,
        json={"plan": "starter"},
    )
    assert checkout.status_code == 200, checkout.text
    body = checkout.json()
    assert body["upgraded"] is True
    assert body["plan"] == "starter"
    assert body["mode"] == "demo"

    plan_after = client.get("/api/v1/organizations/me/billing/plan", headers=headers)
    assert plan_after.json()["plan"] == "starter"


def test_totp_setup_enable_and_login(client: TestClient) -> None:
    email = "totp@example.com"
    password = "SecurePass1"
    _register(client, email=email)

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    setup = client.post("/api/v1/auth/totp/setup", headers=headers)
    assert setup.status_code == 200, setup.text
    secret = setup.json()["secret"]
    code = pyotp.TOTP(secret).now()

    enable = client.post("/api/v1/auth/totp/enable", headers=headers, json={"code": code})
    assert enable.status_code == 200, enable.text

    missing_totp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert missing_totp.status_code == 401
    assert missing_totp.json()["error"]["code"] == "totp_required"

    valid_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "totp_code": pyotp.TOTP(secret).now()},
    )
    assert valid_login.status_code == 200


def test_platform_collect_records_monitoring_metrics(client: TestClient) -> None:
    data = _register(client, email="metrics@example.com")
    token = data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/organizations/me/platforms",
        headers=headers,
        json={
            "connection_type": "docker",
            "name": "Metrics Docker",
            "endpoint": "unix:///var/run/docker.sock",
        },
    )
    assert create.status_code == 201, create.text
    conn_id = create.json()["id"]

    collect = client.post(
        f"/api/v1/organizations/me/platforms/{conn_id}/collect",
        headers=headers,
    )
    assert collect.status_code == 200, collect.text
    assert "monitoring metrics recorded" in collect.json()["message"].lower()

    assets = client.get("/api/v1/organizations/me/assets", headers=headers)
    assert assets.status_code == 200
    platform_assets = [a for a in assets.json() if a.get("asset_type") == "docker_host"]
    assert len(platform_assets) >= 1

    asset_id = platform_assets[0]["id"]
    metrics = client.get(
        f"/api/v1/organizations/me/monitoring/assets/{asset_id}/metrics",
        headers=headers,
    )
    assert metrics.status_code == 200
    types = {m["metric_type"] for m in metrics.json()}
    assert "platform.container.count" in types
