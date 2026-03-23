"""Tests for authentication endpoints."""
import pytest
from tests.conftest import make_user


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "securepass1",
            "full_name": "New User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_register_duplicate_email(self, client, normal_user):
        resp = client.post("/api/v1/auth/register", json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Another User",
        })
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"].lower()

    def test_register_short_password(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "short@example.com",
            "password": "short",
            "full_name": "Short Pass",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Bad Email",
        })
        assert resp.status_code == 422

    def test_register_short_name(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "shortname@example.com",
            "password": "password123",
            "full_name": "A",
        })
        assert resp.status_code == 422

    def test_register_with_referral_code(self, client, normal_user):
        resp = client.post("/api/v1/auth/register", json={
            "email": "referred@example.com",
            "password": "password123",
            "full_name": "Referred User",
            "referral_code": normal_user.referral_code,
        })
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client, normal_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "user@example.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self, client, normal_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "user@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "ghost@example.com",
            "password": "password123",
        })
        assert resp.status_code == 401

    def test_login_suspended_account(self, client, db):
        make_user(db, email="suspended@example.com", password="password123", is_active=False)
        resp = client.post("/api/v1/auth/login", json={
            "email": "suspended@example.com",
            "password": "password123",
        })
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------

class TestRefreshToken:
    def test_refresh_success(self, client, normal_user):
        from backend.utils.encryption import create_refresh_token
        rt = create_refresh_token({"sub": normal_user.id})
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_with_access_token(self, client, user_token):
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": user_token})
        assert resp.status_code == 401

    def test_refresh_invalid_token(self, client):
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "not.a.token"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_success(self, client, auth_headers):
        resp = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert resp.status_code == 200

    def test_logout_unauthenticated(self, client):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Forgot / reset password
# ---------------------------------------------------------------------------

class TestPasswordReset:
    def test_forgot_password_existing_email(self, client, normal_user):
        resp = client.post("/api/v1/auth/forgot-password", json={"email": "user@example.com"})
        assert resp.status_code == 200
        assert "reset link" in resp.json()["message"].lower()

    def test_forgot_password_unknown_email(self, client):
        # Should still return 200 (prevent enumeration)
        resp = client.post("/api/v1/auth/forgot-password", json={"email": "unknown@example.com"})
        assert resp.status_code == 200

    def test_reset_password_success(self, client, db, normal_user):
        token = "validresettoken123"
        normal_user.password_reset_token = token
        db.commit()

        resp = client.post("/api/v1/auth/reset-password", json={
            "token": token,
            "new_password": "newpassword456",
        })
        assert resp.status_code == 200

    def test_reset_password_invalid_token(self, client):
        resp = client.post("/api/v1/auth/reset-password", json={
            "token": "badtoken",
            "new_password": "newpassword456",
        })
        assert resp.status_code == 400

    def test_reset_password_too_short(self, client, db, normal_user):
        normal_user.password_reset_token = "shortpwdtoken"
        db.commit()
        resp = client.post("/api/v1/auth/reset-password", json={
            "token": "shortpwdtoken",
            "new_password": "short",
        })
        assert resp.status_code == 400
