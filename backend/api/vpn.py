"""VPN management API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.models.database import get_db, Server, ServerStatus, Subscription, VPNConfig
from backend.api.auth import get_current_user
from backend.models.database import User
from backend.services.vpn_manager import vpn_manager
from backend.utils.helpers import bytes_to_gb

router = APIRouter()


@router.get("/servers")
async def list_servers(db: Session = Depends(get_db)):
    """List all available VPN servers."""
    servers = db.query(Server).filter(
        Server.status == ServerStatus.ONLINE
    ).order_by(Server.sort_order, Server.latency_ms).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "location": s.location,
            "country_code": s.country_code,
            "flag": s.flag,
            "latency_ms": s.latency_ms,
            "load_percent": s.load_percent,
            "protocols": s.protocols or [],
            "is_china_optimized": s.is_china_optimized,
            "status": s.status.value,
            "bandwidth_gbps": s.bandwidth_gbps,
        }
        for s in servers
    ]


@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get VPN usage statistics for current user."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.is_active == True
    ).order_by(Subscription.expires_at.desc()).first()

    config = db.query(VPNConfig).filter(VPNConfig.user_id == current_user.id).first()

    live_stats = {"upload_bytes": 0, "download_bytes": 0, "total_bytes": 0}
    if config:
        try:
            client_email = f"mc_{current_user.id[:8]}"
            live_stats = await vpn_manager.get_user_traffic(client_email)
        except Exception:
            pass

    return {
        "data_used_bytes": subscription.data_used_bytes if subscription else 0,
        "data_used_gb": bytes_to_gb(subscription.data_used_bytes) if subscription else 0,
        "data_limit_gb": None if not subscription else (
            50 if subscription.plan.value == "basic" else
            150 if subscription.plan.value == "standard" else None
        ),
        "live_upload_bytes": live_stats["upload_bytes"],
        "live_download_bytes": live_stats["download_bytes"],
        "live_total_bytes": live_stats["total_bytes"],
        "live_upload_gb": bytes_to_gb(live_stats["upload_bytes"]),
        "live_download_gb": bytes_to_gb(live_stats["download_bytes"]),
    }


@router.post("/connect")
async def connect_vpn(
    server_id: int,
    protocol: str = "vless_reality",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record VPN connection (client does actual connecting)."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server or server.status != ServerStatus.ONLINE:
        return {"success": False, "message": "Server not available"}

    config = db.query(VPNConfig).filter(VPNConfig.user_id == current_user.id).first()
    if not config:
        return {"success": False, "message": "No VPN config found"}

    protocol_links = {
        "vless_reality": config.vless_reality_link,
        "vmess_ws": config.vmess_ws_link,
        "trojan_grpc": config.trojan_grpc_link,
        "shadowsocks": config.shadowsocks_link,
    }

    link = protocol_links.get(protocol, config.vless_reality_link)
    return {
        "success": True,
        "server": server.name,
        "protocol": protocol,
        "config_link": link,
        "message": "Import this config into your VPN client to connect"
    }
