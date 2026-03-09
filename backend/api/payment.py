"""Payment API endpoints with bKash, Nagad, Stripe support."""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.models.database import (
    get_db, User, Payment, Subscription, PromoCode,
    PaymentStatus, PaymentMethod, PlanType
)
from backend.api.auth import get_current_user
from backend.utils.helpers import calculate_expiry, get_plan_device_limit, get_plan_data_limit_gb, gb_to_bytes
from backend.services.currency_exchange import currency_service
from backend.services.email_service import send_payment_confirmation
from backend.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class CreatePaymentRequest(BaseModel):
    plan: str  # basic, standard, premium
    duration_months: int  # 1, 3, or 6
    payment_method: str  # bkash, nagad, stripe, crypto_btc, etc.
    currency: str = "BDT"
    phone: Optional[str] = None
    promo_code: Optional[str] = None


class VerifyPaymentRequest(BaseModel):
    payment_id: str
    transaction_id: str


async def activate_subscription(
    user_id: str,
    plan: str,
    duration_months: int,
    payment_id: str,
    db: Session
):
    """Activate a subscription after successful payment."""
    # Deactivate existing subscriptions
    db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.is_active == True
    ).update({"is_active": False})

    limit_gb = get_plan_data_limit_gb(plan)
    devices = get_plan_device_limit(plan)

    sub = Subscription(
        user_id=user_id,
        plan=PlanType(plan),
        duration_months=duration_months,
        expires_at=calculate_expiry(duration_months),
        is_active=True,
        data_limit_gb=limit_gb,
        data_used_bytes=0,
        devices_limit=devices,
        payment_id=payment_id,
    )
    db.add(sub)
    db.commit()
    return sub


@router.post("/create")
async def create_payment(
    data: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new payment."""
    # Validate plan
    valid_plans = ["basic", "standard", "premium"]
    if data.plan not in valid_plans:
        raise HTTPException(status_code=400, detail="Invalid plan")
    if data.duration_months not in [1, 3, 6]:
        raise HTTPException(status_code=400, detail="Duration must be 1, 3, or 6 months")

    # Get price
    price = await currency_service.get_plan_price(data.plan, data.currency)
    discount = 0.0

    # Apply promo code
    promo = None
    if data.promo_code:
        promo = db.query(PromoCode).filter(
            PromoCode.code == data.promo_code.upper(),
            PromoCode.is_active == True
        ).first()
        if promo:
            now = datetime.utcnow()
            if promo.valid_until and promo.valid_until < now:
                promo = None
            elif promo.max_uses and promo.uses_count >= promo.max_uses:
                promo = None
            else:
                if promo.discount_percent:
                    discount = price * promo.discount_percent / 100
                elif promo.discount_fixed_usd:
                    discount = await currency_service.convert(promo.discount_fixed_usd, "USD", data.currency)
                discount = min(discount, price)

    final_price = round(price - discount, 2)

    # Validate payment method
    method_map = {
        "bkash": PaymentMethod.BKASH,
        "nagad": PaymentMethod.NAGAD,
        "stripe": PaymentMethod.STRIPE,
        "crypto_btc": PaymentMethod.CRYPTO_BTC,
        "crypto_eth": PaymentMethod.CRYPTO_ETH,
        "crypto_usdt": PaymentMethod.CRYPTO_USDT,
    }
    if data.payment_method not in method_map:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    payment = Payment(
        user_id=current_user.id,
        amount=final_price,
        currency=data.currency,
        method=method_map[data.payment_method],
        status=PaymentStatus.PENDING,
        plan=PlanType(data.plan),
        duration_months=data.duration_months,
        promo_code_id=promo.id if promo else None,
        discount_amount=discount,
        phone=data.phone,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Build gateway URL based on method
    gateway_url = None
    gateway_data = {}

    if data.payment_method == "bkash":
        gateway_data = {
            "merchant_number": settings.bkash_username or "01XXXXXXXXX",
            "amount": final_price,
            "reference": payment.id,
            "instructions": f"Send ৳{final_price} to {settings.bkash_username}, reference: {payment.id[:8]}"
        }
    elif data.payment_method == "nagad":
        gateway_data = {
            "merchant_id": settings.nagad_merchant_id,
            "amount": final_price,
            "reference": payment.id,
            "instructions": f"Pay ৳{final_price} via Nagad, reference: {payment.id[:8]}"
        }
    elif data.payment_method == "stripe":
        try:
            import stripe
            stripe.api_key = settings.stripe_secret_key
            # Convert to USD cents
            usd_amount = await currency_service.convert(final_price, data.currency, "USD")
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": f"MAMA CHOL VPN — {data.plan.title()} Plan"},
                        "unit_amount": int(usd_amount * 100),
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=f"{settings.app_url}/dashboard/payments?success=1&payment_id={payment.id}",
                cancel_url=f"{settings.app_url}/dashboard/payments?cancelled=1",
                metadata={"payment_id": payment.id},
            )
            gateway_url = session.url
            payment.gateway_transaction_id = session.id
            db.commit()
        except Exception as e:
            logger.error(f"Stripe session creation failed: {e}")
            raise HTTPException(status_code=500, detail="Payment gateway error")
    else:
        # Crypto
        crypto_addresses = {
            "crypto_btc": "bc1q_your_bitcoin_address",
            "crypto_eth": "0x_your_ethereum_address",
            "crypto_usdt": "T_your_tron_usdt_address",
        }
        gateway_data = {
            "address": crypto_addresses.get(data.payment_method, ""),
            "amount": final_price,
            "currency": data.currency,
            "reference": payment.id[:16],
            "instructions": f"Send exactly {final_price} {data.currency} to the address above with reference: {payment.id[:16]}"
        }

    return {
        "payment_id": payment.id,
        "amount": final_price,
        "original_amount": price,
        "discount": discount,
        "currency": data.currency,
        "method": data.payment_method,
        "gateway_url": gateway_url,
        "gateway_data": gateway_data,
        "expires_at": None,
        "status": "pending"
    }


@router.get("/history")
async def payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 20
):
    """Get payment history for current user."""
    offset = (page - 1) * limit
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()

    total = db.query(Payment).filter(Payment.user_id == current_user.id).count()

    return {
        "payments": [
            {
                "id": p.id,
                "amount": p.amount,
                "currency": p.currency,
                "method": p.method.value,
                "status": p.status.value,
                "plan": p.plan.value,
                "duration_months": p.duration_months,
                "created_at": p.created_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            }
            for p in payments
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Handle Stripe payment webhooks."""
    import stripe
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        payment_id = session_obj.get("metadata", {}).get("payment_id")
        if payment_id:
            payment = db.query(Payment).filter(Payment.id == payment_id).first()
            if payment and payment.status == PaymentStatus.PENDING:
                payment.status = PaymentStatus.COMPLETED
                payment.gateway_transaction_id = session_obj["id"]
                payment.completed_at = datetime.utcnow()
                db.commit()

                sub = await activate_subscription(
                    payment.user_id, payment.plan.value,
                    payment.duration_months, payment.id, db
                )
                user = db.query(User).filter(User.id == payment.user_id).first()
                if user:
                    background_tasks.add_task(
                        send_payment_confirmation,
                        user.email, user.full_name, payment.plan.value,
                        payment.amount, payment.currency,
                        sub.expires_at.strftime("%Y-%m-%d"), payment.id
                    )
    return {"received": True}


@router.post("/verify/{payment_id}")
async def verify_payment(
    payment_id: str,
    transaction_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually verify a bKash/Nagad payment by transaction ID."""
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != PaymentStatus.PENDING:
        return {"status": payment.status.value, "message": "Payment already processed"}

    # In production, verify with gateway API
    # For now, record the transaction ID for admin review
    payment.gateway_transaction_id = transaction_id
    payment.gateway_response = {"manual_verification": True, "submitted_at": datetime.utcnow().isoformat()}
    db.commit()

    return {
        "payment_id": payment.id,
        "status": "pending_verification",
        "message": "Transaction ID submitted. Your plan will be activated within 30 minutes after verification."
    }
