"""Helper utilities for MAMA CHOL VPN."""
import uuid
import random
import string
import re
from datetime import datetime, timedelta
from typing import Optional
import qrcode
import qrcode.image.svg
import io
import base64


def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def generate_referral_code(length: int = 8) -> str:
    """Generate a unique referral code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


def calculate_expiry(duration_months: int) -> datetime:
    """Calculate subscription expiry date."""
    now = datetime.utcnow()
    # Add months properly
    month = now.month - 1 + duration_months
    year = now.year + month // 12
    month = month % 12 + 1
    import calendar
    day = min(now.day, calendar.monthrange(year, month)[1])
    return now.replace(year=year, month=month, day=day)


def format_bytes(bytes_count: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def bytes_to_gb(bytes_count: int) -> float:
    """Convert bytes to GB."""
    return round(bytes_count / (1024 ** 3), 2)


def gb_to_bytes(gb: float) -> int:
    """Convert GB to bytes."""
    return int(gb * (1024 ** 3))


def generate_qr_code_base64(data: str) -> str:
    """Generate QR code and return as base64 PNG."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return "data:image/png;base64," + base64.b64encode(buffer.read()).decode()


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_bd(phone: str) -> bool:
    """Validate Bangladeshi phone number."""
    pattern = r'^(?:\+88)?01[3-9]\d{8}$'
    return bool(re.match(pattern, phone.replace('-', '').replace(' ', '')))


def mask_email(email: str) -> str:
    """Mask email for privacy display."""
    parts = email.split('@')
    if len(parts) != 2:
        return email
    local = parts[0]
    masked = local[:2] + '*' * (len(local) - 2) if len(local) > 2 else local
    return f"{masked}@{parts[1]}"


def mask_phone(phone: str) -> str:
    """Mask phone number for display."""
    if len(phone) >= 4:
        return phone[:-4] + '****'
    return '****'


def get_plan_data_limit_gb(plan: str) -> Optional[int]:
    """Get data limit in GB for a plan."""
    limits = {"basic": 50, "standard": 150, "premium": None}  # None = unlimited
    return limits.get(plan)


def get_plan_device_limit(plan: str) -> int:
    """Get device limit for a plan."""
    limits = {"basic": 1, "standard": 3, "premium": 5}
    return limits.get(plan, 1)


def get_plan_price_usd(plan: str) -> float:
    """Get plan price in USD."""
    prices = {"basic": 4.99, "standard": 9.99, "premium": 14.99}
    return prices.get(plan, 0.0)


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize user input string."""
    # Remove null bytes and limit length
    return value.replace('\x00', '').strip()[:max_length]
