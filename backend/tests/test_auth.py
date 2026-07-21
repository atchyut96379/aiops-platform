from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_opaque_token
from app.models.user import EmailVerificationToken, PasswordResetToken


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


def test_register_and_login(client: TestClient) -> None:
    data = _register(client)
    assert data["user"]["email"] == "admin@example.com"
    assert data["organization"]["name"].startswith("Acme")
    assert data["tokens"]["access_token"]
    assert data["tokens"]["refresh_token"]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "SecurePass1"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_me_profile(client: TestClient) -> None:
    data = _register(client, email="profile@example.com")
    token = data["tokens"]["access_token"]
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "profile@example.com"
    assert len(body["memberships"]) == 1
    assert body["memberships"][0]["role_name"] == "organization_admin"


def test_refresh_and_logout(client: TestClient) -> None:
    data = _register(client, email="refresh@example.com")
    refresh_token = data["tokens"]["refresh_token"]

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["refresh_token"]

    # Old refresh should no longer work after rotation
    stale = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert stale.status_code == 401

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh})
    assert logout.status_code == 200

    after_logout = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert after_logout.status_code == 401


def test_change_password(client: TestClient) -> None:
    data = _register(client, email="change@example.com")
    token = data["tokens"]["access_token"]

    response = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "SecurePass1", "new_password": "NewSecure2"},
    )
    assert response.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "change@example.com", "password": "SecurePass1"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "change@example.com", "password": "NewSecure2"},
    )
    assert new_login.status_code == 200


def test_password_reset_flow(client: TestClient, db: Session) -> None:
    data = _register(client, email="reset@example.com")
    user_id = data["user"]["id"]

    client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})

    # Insert a known reset token directly for deterministic testing
    raw = "test-reset-token-value"
    db.add(
        PasswordResetToken(
            user_id=user_id,
            token_hash=hash_opaque_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    db.commit()

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw, "new_password": "ResetPass3"},
    )
    assert reset.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset@example.com", "password": "ResetPass3"},
    )
    assert login.status_code == 200


def test_email_verification(client: TestClient, db: Session) -> None:
    data = _register(client, email="verify@example.com")
    user_id = data["user"]["id"]
    raw = "test-verify-token-value"
    db.add(
        EmailVerificationToken(
            user_id=user_id,
            token_hash=hash_opaque_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
    )
    db.commit()

    response = client.post("/api/v1/auth/verify-email", json={"token": raw})
    assert response.status_code == 200

    token = data["tokens"]["access_token"]
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["is_email_verified"] is True


def test_roles_list(client: TestClient) -> None:
    data = _register(client, email="roles@example.com")
    token = data["tokens"]["access_token"]
    response = client.get("/api/v1/roles", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    names = {role["name"] for role in response.json()}
    assert "organization_admin" in names
    assert "devops_engineer" in names


def test_duplicate_email_rejected(client: TestClient) -> None:
    _register(client, email="dup@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Other",
            "last_name": "User",
            "email": "dup@example.com",
            "password": "SecurePass1",
            "organization_name": "Other Org",
        },
    )
    assert response.status_code == 409
