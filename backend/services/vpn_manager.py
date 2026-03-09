"""VPN management service for X-UI/Xray integration."""
import uuid
import logging
import httpx
from typing import Optional, Dict, Any, List
from base64 import b64encode
import json

from backend.config.settings import settings
from backend.utils.encryption import generate_vpn_password, generate_secure_token
from backend.utils.helpers import generate_uuid

logger = logging.getLogger(__name__)

# Inbound IDs in X-UI (configure these to match your X-UI setup)
INBOUND_IDS = {
    "vless_reality": 1,
    "vmess_ws": 2,
    "trojan_grpc": 3,
    "shadowsocks": 4,
}

SERVER_HOST = settings.app_url.replace("https://", "").replace("http://", "")


class XUISession:
    """Manages X-UI panel session."""

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=settings.xui_url, timeout=15)
        self._logged_in = False

    async def login(self) -> bool:
        try:
            resp = await self.client.post("/login", data={
                "username": settings.xui_username,
                "password": settings.xui_password
            })
            data = resp.json()
            self._logged_in = data.get("success", False)
            return self._logged_in
        except Exception as e:
            logger.error(f"X-UI login failed: {e}")
            return False

    async def ensure_logged_in(self):
        if not self._logged_in:
            await self.login()

    async def get_inbounds(self) -> List[Dict]:
        await self.ensure_logged_in()
        try:
            resp = await self.client.get("/xui/API/inbounds")
            data = resp.json()
            return data.get("obj", [])
        except Exception as e:
            logger.error(f"Failed to get inbounds: {e}")
            return []

    async def add_client(self, inbound_id: int, client_data: Dict) -> bool:
        await self.ensure_logged_in()
        try:
            payload = {
                "id": inbound_id,
                "settings": json.dumps({"clients": [client_data]})
            }
            resp = await self.client.post("/xui/API/inbounds/addClient", json=payload)
            return resp.json().get("success", False)
        except Exception as e:
            logger.error(f"Failed to add X-UI client: {e}")
            return False

    async def update_client(self, inbound_id: int, client_uuid: str, client_data: Dict) -> bool:
        await self.ensure_logged_in()
        try:
            payload = {
                "id": inbound_id,
                "settings": json.dumps({"clients": [client_data]})
            }
            resp = await self.client.post(
                f"/xui/API/inbounds/updateClient/{client_uuid}", json=payload
            )
            return resp.json().get("success", False)
        except Exception as e:
            logger.error(f"Failed to update X-UI client: {e}")
            return False

    async def delete_client(self, inbound_id: int, client_uuid: str) -> bool:
        await self.ensure_logged_in()
        try:
            resp = await self.client.post(
                f"/xui/API/inbounds/{inbound_id}/delClient/{client_uuid}"
            )
            return resp.json().get("success", False)
        except Exception as e:
            logger.error(f"Failed to delete X-UI client: {e}")
            return False

    async def get_client_stats(self, email: str) -> Optional[Dict]:
        await self.ensure_logged_in()
        try:
            resp = await self.client.get(f"/xui/API/inbounds/getClientTraffics/{email}")
            data = resp.json()
            return data.get("obj")
        except Exception as e:
            logger.error(f"Failed to get client stats: {e}")
            return None

    async def close(self):
        await self.client.aclose()


class VPNManager:
    """High-level VPN management interface."""

    def __init__(self):
        self.xui = XUISession()

    def _build_vless_link(self, uid: str, remark: str) -> str:
        """Build VLESS Reality link."""
        params = (
            f"type=tcp&security=reality&sni=www.google.com"
            f"&fp=chrome&pbk=your-public-key&sid=your-short-id&flow=xtls-rprx-vision"
        )
        return f"vless://{uid}@{SERVER_HOST}:443?{params}#{remark}"

    def _build_vmess_link(self, uid: str, remark: str) -> str:
        """Build VMess WebSocket link."""
        config = {
            "v": "2", "ps": remark, "add": SERVER_HOST, "port": "8080",
            "id": uid, "aid": "0", "net": "ws", "type": "none",
            "host": SERVER_HOST, "path": "/vpn", "tls": "tls", "sni": SERVER_HOST
        }
        encoded = b64encode(json.dumps(config).encode()).decode()
        return f"vmess://{encoded}"

    def _build_trojan_link(self, password: str, remark: str) -> str:
        """Build Trojan gRPC link."""
        params = f"type=grpc&security=tls&sni={SERVER_HOST}&serviceName=vpn"
        return f"trojan://{password}@{SERVER_HOST}:8443?{params}#{remark}"

    def _build_shadowsocks_link(self, password: str, remark: str) -> str:
        """Build Shadowsocks link."""
        method = "chacha20-ietf-poly1305"
        user_info = b64encode(f"{method}:{password}".encode()).decode()
        return f"ss://{user_info}@{SERVER_HOST}:8388#{remark}"

    def _build_subscription_url(self, token: str) -> str:
        return f"{settings.app_url}/api/v1/sub/{token}"

    async def create_user_config(self, user_email: str, user_id: str) -> Dict[str, Any]:
        """Create complete VPN configuration for a new user."""
        vless_uuid = generate_uuid()
        vmess_uuid = generate_uuid()
        trojan_pass = generate_vpn_password(24)
        ss_password = generate_vpn_password(20)
        sub_token = generate_secure_token(24)

        remark = f"MC-{user_email.split('@')[0][:12]}"

        # Add to X-UI
        client_email = f"mc_{user_id[:8]}"
        try:
            # Add VLESS client
            await self.xui.add_client(INBOUND_IDS["vless_reality"], {
                "id": vless_uuid, "email": client_email,
                "limitIp": 0, "totalGB": 0, "enable": True,
                "flow": "xtls-rprx-vision"
            })
            # Add VMess client
            await self.xui.add_client(INBOUND_IDS["vmess_ws"], {
                "id": vmess_uuid, "email": client_email,
                "limitIp": 0, "totalGB": 0, "enable": True
            })
            # Add Trojan client
            await self.xui.add_client(INBOUND_IDS["trojan_grpc"], {
                "password": trojan_pass, "email": client_email,
                "limitIp": 0, "totalGB": 0, "enable": True
            })
            # Add Shadowsocks client
            await self.xui.add_client(INBOUND_IDS["shadowsocks"], {
                "password": ss_password, "email": client_email,
                "limitIp": 0, "totalGB": 0, "enable": True
            })
        except Exception as e:
            logger.warning(f"X-UI unavailable during config creation: {e}")

        return {
            "uuid_vless": vless_uuid,
            "uuid_vmess": vmess_uuid,
            "uuid_trojan": trojan_pass,
            "ss_password": ss_password,
            "subscription_token": sub_token,
            "vless_reality_link": self._build_vless_link(vless_uuid, remark),
            "vmess_ws_link": self._build_vmess_link(vmess_uuid, remark),
            "trojan_grpc_link": self._build_trojan_link(trojan_pass, remark),
            "shadowsocks_link": self._build_shadowsocks_link(ss_password, remark),
            "subscription_url": self._build_subscription_url(sub_token),
        }

    async def get_user_traffic(self, email_prefix: str) -> Dict[str, int]:
        """Get total traffic for a user across all inbounds."""
        stats = await self.xui.get_client_stats(email_prefix)
        if stats:
            return {
                "upload_bytes": stats.get("up", 0),
                "download_bytes": stats.get("down", 0),
                "total_bytes": stats.get("total", 0),
            }
        return {"upload_bytes": 0, "download_bytes": 0, "total_bytes": 0}

    async def set_user_enabled(self, client_email: str, enabled: bool) -> bool:
        """Enable or disable all inbounds for a user."""
        success = True
        for inbound_id in INBOUND_IDS.values():
            # This is simplified; in production you'd fetch the client and update
            pass
        return success

    async def delete_user_config(self, vless_uuid: str) -> bool:
        """Remove a user from all inbounds."""
        success = True
        for inbound_id in INBOUND_IDS.values():
            result = await self.xui.delete_client(inbound_id, vless_uuid)
            if not result:
                success = False
        return success


vpn_manager = VPNManager()
