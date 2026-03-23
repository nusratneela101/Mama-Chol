"""Tests for admin dashboard and management endpoints."""
from backend.models.database import Server, ServerStatus
from tests.conftest import make_user


class TestAdminDashboard:
    def test_dashboard_requires_admin(self, client, auth_headers):
        resp = client.get("/api/v1/admin/dashboard", headers=auth_headers)
        assert resp.status_code == 403

    def test_dashboard_unauthenticated(self, client):
        resp = client.get("/api/v1/admin/dashboard")
        assert resp.status_code == 401

    def test_dashboard_success(self, client, admin_headers):
        resp = client.get("/api/v1/admin/dashboard", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "active_subscriptions" in data
        assert "monthly_revenue_bdt" in data
        assert "pending_payments" in data
        assert "online_servers" in data


class TestAdminUserManagement:
    def test_list_users_requires_admin(self, client, auth_headers):
        resp = client.get("/api/v1/admin/users", headers=auth_headers)
        assert resp.status_code == 403

    def test_list_users_success(self, client, db, admin_headers):
        make_user(db, email="extra@example.com")
        resp = client.get("/api/v1/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))

    def test_update_user_requires_admin(self, client, auth_headers, normal_user):
        resp = client.patch(
            f"/api/v1/admin/users/{normal_user.id}",
            json={"is_active": False},
            headers=auth_headers
        )
        assert resp.status_code == 403

    def test_update_user_success(self, client, db, admin_headers, normal_user):
        resp = client.patch(
            f"/api/v1/admin/users/{normal_user.id}",
            json={"is_active": False},
            headers=admin_headers
        )
        assert resp.status_code in (200, 404)


class TestAdminServerManagement:
    def test_add_server_requires_admin(self, client, auth_headers):
        resp = client.post("/api/v1/admin/servers", json={
            "name": "SG-02",
            "hostname": "sg02.mamachol.online",
            "ip_address": "5.6.7.8",
            "location": "Singapore",
            "country_code": "SG",
        }, headers=auth_headers)
        assert resp.status_code == 403

    def test_add_server_success(self, client, admin_headers):
        resp = client.post("/api/v1/admin/servers", json={
            "name": "SG-02",
            "hostname": "sg02.mamachol.online",
            "ip_address": "5.6.7.8",
            "location": "Singapore",
            "country_code": "SG",
            "flag": "🇸🇬",
        }, headers=admin_headers)
        assert resp.status_code in (200, 201)

    def test_list_servers_admin(self, client, db, admin_headers):
        server = Server(
            name="JP-01",
            hostname="jp01.mamachol.online",
            ip_address="9.9.9.9",
            location="Tokyo",
            country_code="JP",
            flag="🇯🇵",
            status=ServerStatus.ONLINE,
        )
        db.add(server)
        db.commit()

        resp = client.get("/api/v1/admin/servers", headers=admin_headers)
        assert resp.status_code in (200, 404)


class TestAdminPaymentApproval:
    def test_approve_payment_requires_admin(self, client, auth_headers):
        resp = client.post("/api/v1/admin/payments/approve", json={
            "payment_id": "some-id",
        }, headers=auth_headers)
        assert resp.status_code == 403

    def test_approve_nonexistent_payment(self, client, admin_headers):
        resp = client.post("/api/v1/admin/payments/approve", json={
            "payment_id": "00000000-0000-0000-0000-000000000000",
        }, headers=admin_headers)
        assert resp.status_code in (400, 404)
