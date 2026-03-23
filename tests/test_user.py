"""Tests for user profile and dashboard endpoints."""
from tests.conftest import make_user


class TestProfile:
    def test_get_profile_authenticated(self, client, auth_headers, normal_user):
        resp = client.get("/api/v1/user/profile", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == normal_user.email
        assert data["full_name"] == normal_user.full_name
        assert "referral_code" in data
        assert "plan" in data

    def test_get_profile_unauthenticated(self, client):
        resp = client.get("/api/v1/user/profile")
        assert resp.status_code == 401

    def test_update_profile_full_name(self, client, auth_headers):
        resp = client.patch("/api/v1/user/profile", json={"full_name": "Updated Name"}, headers=auth_headers)
        assert resp.status_code == 200
        assert "updated" in resp.json()["message"].lower()

    def test_update_profile_language(self, client, auth_headers):
        resp = client.patch("/api/v1/user/profile", json={"language": "bn"}, headers=auth_headers)
        assert resp.status_code == 200

    def test_update_profile_invalid_language(self, client, auth_headers):
        # Invalid language should be silently ignored (no error), profile still updates
        resp = client.patch("/api/v1/user/profile", json={"language": "xx"}, headers=auth_headers)
        assert resp.status_code == 200

    def test_update_profile_telegram_id(self, client, auth_headers):
        resp = client.patch("/api/v1/user/profile", json={"telegram_id": "123456789"}, headers=auth_headers)
        assert resp.status_code == 200


class TestDashboard:
    def test_get_dashboard_authenticated(self, client, auth_headers):
        resp = client.get("/api/v1/user/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "plan" in data
        assert "plan_active" in data
        assert "days_left" in data
        assert "data_used_gb" in data
        assert "recent_payments" in data
        assert isinstance(data["recent_payments"], list)

    def test_get_dashboard_unauthenticated(self, client):
        resp = client.get("/api/v1/user/dashboard")
        assert resp.status_code == 401

    def test_dashboard_no_subscription(self, client, auth_headers):
        resp = client.get("/api/v1/user/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] is None
        assert data["plan_active"] is False
        assert data["days_left"] == 0


class TestVPNConfig:
    def test_get_vpn_config_unauthenticated(self, client):
        resp = client.get("/api/v1/user/vpn-config")
        assert resp.status_code == 401

    def test_regenerate_config_unauthenticated(self, client):
        resp = client.post("/api/v1/user/regenerate-config")
        assert resp.status_code == 401
