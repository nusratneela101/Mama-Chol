"""User API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.models.database import get_db, User, Subscription, VPNConfig, Payment
from backend.api.auth import get_current_user
from backend.services.vpn_manager import vpn_manager
from backend.utils.helpers import (
    generate_qr_code_base64, bytes_to_gb,
    get_plan_data_limit_gb, get_plan_device_limit, format_bytes
)
from datetime import datetime

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    language: Optional[str] = None
    telegram_id: Optional[str] = None


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.is_active == True
    ).order_by(Subscription.expires_at.desc()).first()

    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "language": current_user.language,
        "referral_code": current_user.referral_code,
        "telegram_id": current_user.telegram_id,
        "plan": subscription.plan.value if subscription else None,
        "plan_expires_at": subscription.expires_at.isoformat() if subscription else None,
        "plan_active": bool(subscription and subscription.expires_at > datetime.utcnow()),
        "data_used_bytes": subscription.data_used_bytes if subscription else 0,
        "data_used_gb": bytes_to_gb(subscription.data_used_bytes) if subscription else 0,
        "data_limit_gb": get_plan_data_limit_gb(subscription.plan.value) if subscription else 0,
        "devices_limit": get_plan_device_limit(subscription.plan.value) if subscription else 0,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
    }


@router.patch("/profile")
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    if data.full_name:
        current_user.full_name = data.full_name[:100]
    if data.language and data.language in ["en", "bn", "zh", "hi", "ar"]:
        current_user.language = data.language
    if data.telegram_id is not None:
        current_user.telegram_id = data.telegram_id

    db.commit()
    return {"message": "Profile updated successfully"}


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.is_active == True
    ).order_by(Subscription.expires_at.desc()).first()

    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).limit(5).all()

    days_left = 0
    data_percent = 0
    if subscription:
        delta = subscription.expires_at - datetime.utcnow()
        days_left = max(0, delta.days)
        limit = get_plan_data_limit_gb(subscription.plan.value)
        if limit:
            data_percent = min(100, round((bytes_to_gb(subscription.data_used_bytes) / limit) * 100))

    return {
        "plan": subscription.plan.value if subscription else None,
        "plan_active": bool(subscription and subscription.expires_at > datetime.utcnow()),
        "days_left": days_left,
        "expires_at": subscription.expires_at.isoformat() if subscription else None,
        "data_used_gb": bytes_to_gb(subscription.data_used_bytes) if subscription else 0,
        "data_used_formatted": format_bytes(subscription.data_used_bytes) if subscription else "0 B",
        "data_limit_gb": get_plan_data_limit_gb(subscription.plan.value) if subscription else 0,
        "data_percent": data_percent,
        "devices_limit": get_plan_device_limit(subscription.plan.value) if subscription else 0,
        "recent_payments": [
            {
                "id": p.id, "amount": p.amount, "currency": p.currency,
                "method": p.method.value, "status": p.status.value,
                "plan": p.plan.value, "created_at": p.created_at.isoformat()
            } for p in payments
        ]
    }


@router.get("/vpn-config")
async def get_vpn_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get or create VPN configuration for user."""
    config = db.query(VPNConfig).filter(VPNConfig.user_id == current_user.id).first()

    if not config:
        # Create new config
        config_data = await vpn_manager.create_user_config(current_user.email, current_user.id)
        config = VPNConfig(
            user_id=current_user.id,
            **config_data
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    # Generate QR code for subscription URL
    subscription_url = f"https://mamachol.online/api/v1/sub/{config.subscription_token}"
    qr_base64 = generate_qr_code_base64(subscription_url)

    return {
        "vless_reality_link": config.vless_reality_link,
        "vmess_ws_link": config.vmess_ws_link,
        "trojan_grpc_link": config.trojan_grpc_link,
        "shadowsocks_link": config.shadowsocks_link,
        "subscription_url": subscription_url,
        "qr_code_base64": qr_base64,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


@router.post("/regenerate-config")
async def regenerate_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate VPN configuration (creates new keys)."""
    # Delete old config from X-UI
    old_config = db.query(VPNConfig).filter(VPNConfig.user_id == current_user.id).first()
    if old_config and old_config.uuid_vless:
        await vpn_manager.delete_user_config(old_config.uuid_vless)

    # Create new config
    config_data = await vpn_manager.create_user_config(current_user.email, current_user.id)

    if old_config:
        for key, value in config_data.items():
            setattr(old_config, key, value)
        db.commit()
    else:
        new_config = VPNConfig(user_id=current_user.id, **config_data)
        db.add(new_config)
        db.commit()

    return {"message": "VPN configuration regenerated successfully. Update your client with the new config."}
