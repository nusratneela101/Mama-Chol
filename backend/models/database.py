"""SQLAlchemy models for MAMA CHOL VPN."""
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean,
    DateTime, Text, ForeignKey, Enum, JSON, BigInteger
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from backend.config.settings import settings

engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.debug,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_uuid():
    return str(uuid.uuid4())


class PlanType(str, enum.Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    BKASH = "bkash"
    NAGAD = "nagad"
    STRIPE = "stripe"
    CRYPTO_BTC = "crypto_btc"
    CRYPTO_ETH = "crypto_eth"
    CRYPTO_USDT = "crypto_usdt"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ServerStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    language = Column(String(5), default="en")
    telegram_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    subscriptions = relationship("Subscription", back_populates="user")
    vpn_configs = relationship("VPNConfig", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    tickets = relationship("SupportTicket", back_populates="user")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(Enum(PlanType), nullable=False)
    duration_months = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    data_limit_gb = Column(Integer, nullable=True)
    data_used_bytes = Column(BigInteger, default=0)
    devices_limit = Column(Integer, default=1)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=True)
    auto_renew = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    payment = relationship("Payment", foreign_keys=[payment_id])


class VPNConfig(Base):
    __tablename__ = "vpn_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    xui_client_id = Column(String(100), nullable=True)
    uuid_vless = Column(String(36), nullable=True)
    uuid_vmess = Column(String(36), nullable=True)
    uuid_trojan = Column(String(100), nullable=True)
    ss_password = Column(String(100), nullable=True)
    subscription_token = Column(String(100), unique=True, nullable=True)
    vless_reality_link = Column(Text, nullable=True)
    vmess_ws_link = Column(Text, nullable=True)
    trojan_grpc_link = Column(Text, nullable=True)
    shadowsocks_link = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="vpn_configs")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    amount_usd = Column(Float, nullable=True)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    plan = Column(Enum(PlanType), nullable=False)
    duration_months = Column(Integer, nullable=False)
    gateway_transaction_id = Column(String(255), nullable=True)
    gateway_response = Column(JSON, nullable=True)
    promo_code_id = Column(String(36), ForeignKey("promo_codes.id"), nullable=True)
    discount_amount = Column(Float, default=0)
    phone = Column(String(20), nullable=True)
    crypto_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")
    promo_code = relationship("PromoCode")


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)
    location = Column(String(100), nullable=False)
    country_code = Column(String(5), nullable=False)
    flag = Column(String(10), nullable=False, default="🌍")
    xui_url = Column(String(255), nullable=True)
    xui_username = Column(String(100), nullable=True)
    xui_password = Column(String(100), nullable=True)
    ssh_port = Column(Integer, default=22)
    status = Column(Enum(ServerStatus), default=ServerStatus.ONLINE)
    is_china_optimized = Column(Boolean, default=False)
    protocols = Column(JSON, default=list)
    load_percent = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    bandwidth_gbps = Column(Float, default=1.0)
    sort_order = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(String(20), default="normal")
    admin_reply = Column(Text, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="tickets")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    discount_percent = Column(Integer, nullable=True)
    discount_fixed_usd = Column(Float, nullable=True)
    max_uses = Column(Integer, nullable=True)
    uses_count = Column(Integer, default=0)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)
