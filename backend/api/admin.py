"""Admin API endpoints."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.models.database import (
    get_db, User, Subscription, Payment, Server,
    PaymentStatus, PaymentMethod, ServerStatus, SupportTicket, TicketStatus
)
from backend.api.auth import get_admin_user
from backend.utils.helpers import bytes_to_gb, get_plan_device_limit, get_plan_data_limit_gb, gb_to_bytes

router = APIRouter()


class UpdateUserRequest(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    plan: Optional[str] = None
    extend_days: Optional[int] = None


class AddServerRequest(BaseModel):
    name: str
    hostname: str
    ip_address: str
    location: str
    country_code: str
    flag: str = "🌍"
    is_china_optimized: bool = False
    protocols: list = []
    bandwidth_gbps: float = 1.0
    sort_order: int = 100


class ApprovePaymentRequest(BaseModel):
    payment_id: str
    notes: Optional[str] = None


@router.get("/dashboard")
async def admin_dashboard(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard metrics."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)

    total_users = db.query(func.count(User.id)).scalar()
    active_subs = db.query(func.count(Subscription.id)).filter(
        Subscription.is_active == True,
        Subscription.expires_at > now
    ).scalar()

    monthly_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.COMPLETED,
        Payment.created_at >= month_start
    ).scalar() or 0

    pending_payments = db.query(func.count(Payment.id)).filter(
        Payment.status == PaymentStatus.PENDING
    ).scalar()

    open_tickets = db.query(func.count(SupportTicket.id)).filter(
        SupportTicket.status == TicketStatus.OPEN
    ).scalar()

    online_servers = db.query(func.count(Server.id)).filter(
        Server.status == ServerStatus.ONLINE
    ).scalar()

    # Revenue by method
    revenue_by_method = db.query(
        Payment.method, func.sum(Payment.amount).label("total")
    ).filter(
        Payment.status == PaymentStatus.COMPLETED,
        Payment.created_at >= month_start
    ).group_by(Payment.method).all()

    return {
        "total_users": total_users,
        "active_subscriptions": active_subs,
        "monthly_revenue_bdt": round(float(monthly_revenue), 2),
        "pending_payments": pending_payments,
        "open_support_tickets": open_tickets,
        "online_servers": online_servers,
        "revenue_by_method": [
            {"method": r.method.value, "total": float(r.total or 0)}
            for r in revenue_by_method
        ],
    }


@router.get("/users")
async def list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None
):
    """List all users with pagination and filtering."""
    query = db.query(User)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) | (User.full_name.ilike(search_term))
        )
    if status == "active":
        query = query.filter(User.is_active == True)
    elif status == "suspended":
        query = query.filter(User.is_active == False)

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for u in users:
        sub = db.query(Subscription).filter(
            Subscription.user_id == u.id, Subscription.is_active == True
        ).order_by(Subscription.expires_at.desc()).first()

        result.append({
            "id": u.id, "email": u.email, "full_name": u.full_name,
            "is_active": u.is_active, "is_admin": u.is_admin,
            "is_verified": u.is_verified, "language": u.language,
            "plan": sub.plan.value if sub else None,
            "plan_expires": sub.expires_at.isoformat() if sub else None,
            "created_at": u.created_at.isoformat(),
            "last_login": u.last_login.isoformat() if u.last_login else None,
        })

    return {"users": result, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UpdateUserRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_admin is not None:
        user.is_admin = data.is_admin

    if data.plan:
        sub = db.query(Subscription).filter(
            Subscription.user_id == user_id, Subscription.is_active == True
        ).first()
        from backend.models.database import PlanType
        if sub:
            sub.plan = PlanType(data.plan)
            sub.devices_limit = get_plan_device_limit(data.plan)
            new_limit = get_plan_data_limit_gb(data.plan)
            sub.data_limit_gb = new_limit

    if data.extend_days:
        sub = db.query(Subscription).filter(
            Subscription.user_id == user_id, Subscription.is_active == True
        ).first()
        if sub:
            base = max(sub.expires_at, datetime.utcnow())
            sub.expires_at = base + timedelta(days=data.extend_days)

    db.commit()
    return {"message": "User updated successfully"}


@router.get("/payments")
async def list_payments(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None
):
    """List all payments."""
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == PaymentStatus(status))

    total = query.count()
    payments = query.order_by(Payment.created_at.desc()).offset((page-1)*limit).limit(limit).all()

    return {
        "payments": [
            {
                "id": p.id, "user_id": p.user_id,
                "amount": p.amount, "currency": p.currency,
                "method": p.method.value, "status": p.status.value,
                "plan": p.plan.value, "duration_months": p.duration_months,
                "gateway_transaction_id": p.gateway_transaction_id,
                "phone": p.phone,
                "created_at": p.created_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            }
            for p in payments
        ],
        "total": total, "page": page, "pages": (total + limit - 1) // limit
    }


@router.post("/payments/approve")
async def approve_payment(
    data: ApprovePaymentRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Manually approve a payment (for bKash/Nagad offline verification)."""
    from backend.api.payment import activate_subscription
    payment = db.query(Payment).filter(Payment.id == data.payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == PaymentStatus.COMPLETED:
        return {"message": "Payment already completed"}

    payment.status = PaymentStatus.COMPLETED
    payment.completed_at = datetime.utcnow()
    payment.gateway_response = {
        "manually_approved": True,
        "approved_by": admin.email,
        "notes": data.notes,
        "approved_at": datetime.utcnow().isoformat()
    }
    db.commit()

    await activate_subscription(
        payment.user_id, payment.plan.value, payment.duration_months, payment.id, db
    )

    return {"message": f"Payment {data.payment_id} approved and subscription activated"}


@router.get("/servers")
async def list_servers(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """List all servers."""
    servers = db.query(Server).order_by(Server.sort_order).all()
    return [
        {
            "id": s.id, "name": s.name, "location": s.location,
            "country_code": s.country_code, "flag": s.flag,
            "ip_address": s.ip_address, "status": s.status.value,
            "load_percent": s.load_percent, "latency_ms": s.latency_ms,
            "is_china_optimized": s.is_china_optimized,
            "protocols": s.protocols, "created_at": s.created_at.isoformat()
        }
        for s in servers
    ]


@router.post("/servers")
async def add_server(
    data: AddServerRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Add a new VPN server."""
    server = Server(
        name=data.name, hostname=data.hostname, ip_address=data.ip_address,
        location=data.location, country_code=data.country_code, flag=data.flag,
        is_china_optimized=data.is_china_optimized, protocols=data.protocols,
        bandwidth_gbps=data.bandwidth_gbps, sort_order=data.sort_order,
        status=ServerStatus.ONLINE
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return {"message": "Server added successfully", "id": server.id}


@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Remove a server."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    db.delete(server)
    db.commit()
    return {"message": "Server deleted"}


@router.get("/analytics")
async def get_analytics(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get platform analytics."""
    now = datetime.utcnow()
    start = now - timedelta(days=days)

    new_users = db.query(func.count(User.id)).filter(User.created_at >= start).scalar()
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.COMPLETED,
        Payment.created_at >= start
    ).scalar() or 0

    revenue_by_plan = db.query(
        Payment.plan, func.sum(Payment.amount).label("total"), func.count(Payment.id).label("count")
    ).filter(
        Payment.status == PaymentStatus.COMPLETED,
        Payment.created_at >= start
    ).group_by(Payment.plan).all()

    users_by_lang = db.query(
        User.language, func.count(User.id).label("count")
    ).group_by(User.language).all()

    return {
        "period_days": days,
        "new_users": new_users,
        "total_revenue_bdt": round(float(total_revenue), 2),
        "revenue_by_plan": [
            {"plan": r.plan.value, "total": float(r.total or 0), "count": r.count}
            for r in revenue_by_plan
        ],
        "users_by_language": [
            {"language": r.language, "count": r.count}
            for r in users_by_lang
        ],
    }
