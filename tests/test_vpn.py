"""Tests for VPN server and usage endpoints."""
from backend.models.database import Server, ServerStatus, VPNConfig
from tests.conftest import make_user


def _add_server(db, name="SG-01", location="Singapore", country_code="SG",
                status=ServerStatus.ONLINE):
    """Helper to insert a Server row."""
    server = Server(
        name=name,
        hostname=f"{name.lower()}.mamachol.online",
        ip_address="1.2.3.4",
        location=location,
        country_code=country_code,
        flag="🇸🇬",
        status=status,
        protocols=["vless_reality", "vmess_ws"],
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


class TestServerList:
    def test_list_servers_empty(self, client):
        resp = client.get("/api/v1/vpn/servers")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_servers_returns_online_only(self, client, db):
        _add_server(db, name="SG-01", status=ServerStatus.ONLINE)
        _add_server(db, name="JP-01", status=ServerStatus.OFFLINE)

        resp = client.get("/api/v1/vpn/servers")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "SG-01"

    def test_server_list_fields(self, client, db):
        _add_server(db)
        resp = client.get("/api/v1/vpn/servers")
        assert resp.status_code == 200
        server = resp.json()[0]
        for field in ["id", "name", "location", "country_code", "flag",
                      "latency_ms", "load_percent", "protocols", "status"]:
            assert field in server


class TestUsage:
    def test_get_usage_unauthenticated(self, client):
        resp = client.get("/api/v1/vpn/usage")
        assert resp.status_code == 401

    def test_get_usage_no_subscription(self, client, auth_headers):
        resp = client.get("/api/v1/vpn/usage", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data_used_bytes"] == 0
        assert data["data_used_gb"] == 0

    def test_get_usage_authenticated(self, client, auth_headers):
        resp = client.get("/api/v1/vpn/usage", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "live_upload_bytes" in data
        assert "live_download_bytes" in data


class TestConnect:
    def test_connect_unauthenticated(self, client, db):
        server = _add_server(db)
        resp = client.post(f"/api/v1/vpn/connect?server_id={server.id}")
        assert resp.status_code == 401

    def test_connect_no_config(self, client, db, auth_headers):
        server = _add_server(db)
        resp = client.post(f"/api/v1/vpn/connect?server_id={server.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "config" in data["message"].lower()

    def test_connect_offline_server(self, client, db, auth_headers, normal_user):
        server = _add_server(db, status=ServerStatus.OFFLINE)
        resp = client.post(f"/api/v1/vpn/connect?server_id={server.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    def test_connect_with_config(self, client, db, auth_headers, normal_user):
        server = _add_server(db)
        config = VPNConfig(
            user_id=normal_user.id,
            subscription_token="testtoken123",
            vless_reality_link="vless://test-link",
            vmess_ws_link="vmess://test-link",
        )
        db.add(config)
        db.commit()

        resp = client.post(
            f"/api/v1/vpn/connect?server_id={server.id}&protocol=vless_reality",
            headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "config_link" in data
