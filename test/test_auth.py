"""Tests para el módulo Auth: login, register, refresh, logout, rate limiting."""

import pytest
from fastapi.testclient import TestClient

BASE = "/api/v1/auth"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_returns_access_and_refresh_token(client: TestClient):
    resp = client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 30 * 60
    assert body["email"] == ADMIN_EMAIL


def test_login_wrong_password_returns_401(client: TestClient):
    resp = client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient):
    resp = client.post(f"{BASE}/login", json={"email": "nobody@example.com", "password": "x"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def test_register_returns_tokens(client: TestClient):
    resp = client.post(f"{BASE}/register", json={
        "email": "new@example.com",
        "nombre": "Test",
        "apellido": "User",
        "password": "secret123",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["roles"] == ["CLIENT"]


def test_register_duplicate_email_returns_409(client: TestClient):
    payload = {"email": "dup@example.com", "nombre": "A", "apellido": "B", "password": "pass"}
    client.post(f"{BASE}/register", json=payload)
    resp = client.post(f"{BASE}/register", json=payload)
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

def test_refresh_ok(client: TestClient):
    login_resp = client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    refresh_token = login_resp.json()["refresh_token"]
    old_access = login_resp.json()["access_token"]

    resp = client.post(f"{BASE}/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["refresh_token"] == refresh_token  # same refresh token returned

    # Nuevo access token debe ser funcional
    me_resp = client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me_resp.status_code == 200


def test_refresh_invalid_token_returns_401(client: TestClient):
    resp = client.post(f"{BASE}/refresh", json={"refresh_token": "not.a.valid.token"})
    assert resp.status_code == 401


def test_refresh_with_revoked_token_returns_401(client: TestClient):
    login_resp = client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    body = login_resp.json()
    refresh_token = body["refresh_token"]
    access_token = body["access_token"]

    # Revocar via logout
    logout_resp = client.post(
        f"{BASE}/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_resp.status_code == 204

    # Intentar refresh con token revocado → 401
    resp = client.post(f"{BASE}/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def test_logout_returns_204(client: TestClient):
    login_resp = client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    body = login_resp.json()
    resp = client.post(
        f"{BASE}/logout",
        json={"refresh_token": body["refresh_token"]},
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert resp.status_code == 204


def test_logout_without_auth_returns_401(client: TestClient):
    resp = client.post(f"{BASE}/logout", json={"refresh_token": "any"})
    assert resp.status_code == 401


def test_logout_is_idempotent(client: TestClient):
    """Revocar un token ya revocado no debe lanzar error."""
    login_resp = client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    body = login_resp.json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    payload = {"refresh_token": body["refresh_token"]}

    client.post(f"{BASE}/logout", json=payload, headers=headers)
    resp = client.post(f"{BASE}/logout", json=payload, headers=headers)
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Rate limiting — login
# ---------------------------------------------------------------------------

def test_rate_limit_login_returns_429_after_5_failures(client: TestClient):
    for _ in range(5):
        client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": "wrong"})

    resp = client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
    assert int(resp.headers["Retry-After"]) > 0


def test_rate_limit_login_header_retry_after_present(client: TestClient):
    for _ in range(5):
        client.post(f"{BASE}/login", json={"email": "x@x.com", "password": "bad"})

    resp = client.post(f"{BASE}/login", json={"email": "x@x.com", "password": "bad"})
    assert resp.status_code == 429
    retry_after = resp.headers.get("Retry-After")
    assert retry_after is not None
    assert int(retry_after) > 0


def test_rate_limit_successful_login_not_counted(client: TestClient):
    """Un login exitoso no incrementa el contador de fallos."""
    for _ in range(4):
        client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": "wrong"})

    # Login exitoso — no debe contar como fallo
    ok_resp = client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert ok_resp.status_code == 200

    # Con 4 fallos previos, el siguiente fallo (5to) aún no activa el límite
    fail_resp = client.post(f"{BASE}/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
    assert fail_resp.status_code == 401  # no 429 — el login exitoso no contó


# ---------------------------------------------------------------------------
# Rate limiting — register
# ---------------------------------------------------------------------------

def test_rate_limit_register_returns_429_after_5_failures(client: TestClient):
    # Registrar una vez (éxito)
    client.post(f"{BASE}/register", json={
        "email": "unique@example.com", "nombre": "A", "apellido": "B", "password": "pass123"
    })
    # Las siguientes 5 son fallos (email duplicado → 409)
    for _ in range(5):
        client.post(f"{BASE}/register", json={
            "email": "unique@example.com", "nombre": "A", "apellido": "B", "password": "pass123"
        })

    resp = client.post(f"{BASE}/register", json={
        "email": "unique@example.com", "nombre": "A", "apellido": "B", "password": "pass123"
    })
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
