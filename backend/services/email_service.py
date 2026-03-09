"""Email service with Gmail SMTP and HTML templates."""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from jinja2 import Environment, BaseLoader
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# HTML Email Templates
TEMPLATES = {
    "welcome": """
<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#0f0f1a;color:#fff;margin:0;padding:0">
<div style="max-width:600px;margin:0 auto;padding:40px 20px">
<div style="text-align:center;margin-bottom:32px">
  <h1 style="background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:28px">🛡️ MAMA CHOL VPN</h1>
</div>
<div style="background:#1a1a2e;border-radius:16px;padding:32px;border:1px solid rgba(255,255,255,0.08)">
  <h2 style="margin-top:0">Welcome, {{ name }}! 🎉</h2>
  <p style="color:#a0aec0">Your account has been created successfully. You're now part of the MAMA CHOL VPN family!</p>
  <div style="text-align:center;margin:32px 0">
    <a href="{{ app_url }}/dashboard" style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:14px 32px;border-radius:50px;text-decoration:none;font-weight:700">Go to Dashboard →</a>
  </div>
  <p style="color:#a0aec0;font-size:14px">If you didn't create this account, please ignore this email.</p>
</div>
<p style="text-align:center;color:#718096;font-size:12px;margin-top:24px">© 2025 MAMA CHOL VPN • <a href="{{ app_url }}" style="color:#667eea">mamachol.online</a></p>
</div></body></html>
""",
    "payment_confirmation": """
<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#0f0f1a;color:#fff;margin:0;padding:0">
<div style="max-width:600px;margin:0 auto;padding:40px 20px">
<div style="text-align:center;margin-bottom:32px">
  <h1 style="background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:28px">🛡️ MAMA CHOL VPN</h1>
</div>
<div style="background:#1a1a2e;border-radius:16px;padding:32px;border:1px solid rgba(255,255,255,0.08)">
  <h2 style="margin-top:0;color:#48bb78">✅ Payment Confirmed!</h2>
  <p style="color:#a0aec0">Hi {{ name }}, your payment has been processed successfully.</p>
  <div style="background:#0d0d1a;border-radius:12px;padding:20px;margin:20px 0">
    <table style="width:100%;border-collapse:collapse">
      <tr><td style="color:#a0aec0;padding:6px 0">Plan:</td><td style="text-align:right;font-weight:700;text-transform:capitalize">{{ plan }}</td></tr>
      <tr><td style="color:#a0aec0;padding:6px 0">Amount:</td><td style="text-align:right;font-weight:700">{{ amount }} {{ currency }}</td></tr>
      <tr><td style="color:#a0aec0;padding:6px 0">Valid Until:</td><td style="text-align:right;font-weight:700">{{ expiry }}</td></tr>
      <tr><td style="color:#a0aec0;padding:6px 0">Transaction ID:</td><td style="text-align:right;font-size:12px;font-family:monospace">{{ transaction_id }}</td></tr>
    </table>
  </div>
  <div style="text-align:center;margin:24px 0">
    <a href="{{ app_url }}/dashboard/config" style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:14px 32px;border-radius:50px;text-decoration:none;font-weight:700">Get Your VPN Config →</a>
  </div>
</div>
<p style="text-align:center;color:#718096;font-size:12px;margin-top:24px">© 2025 MAMA CHOL VPN</p>
</div></body></html>
""",
    "subscription_expiring": """
<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#0f0f1a;color:#fff;margin:0;padding:0">
<div style="max-width:600px;margin:0 auto;padding:40px 20px">
<div style="background:#1a1a2e;border-radius:16px;padding:32px;border:1px solid rgba(255,255,255,0.08)">
  <h2 style="margin-top:0;color:#f6ad55">⚠️ Your Subscription Expires in {{ days }} Days</h2>
  <p style="color:#a0aec0">Hi {{ name }}, don't let your VPN access expire! Renew now to keep your internet private and unrestricted.</p>
  <div style="text-align:center;margin:24px 0">
    <a href="{{ app_url }}/dashboard/payments" style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:14px 32px;border-radius:50px;text-decoration:none;font-weight:700">Renew Now →</a>
  </div>
</div>
</div></body></html>
""",
    "password_reset": """
<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#0f0f1a;color:#fff;margin:0;padding:0">
<div style="max-width:600px;margin:0 auto;padding:40px 20px">
<div style="background:#1a1a2e;border-radius:16px;padding:32px;border:1px solid rgba(255,255,255,0.08)">
  <h2 style="margin-top:0">🔑 Reset Your Password</h2>
  <p style="color:#a0aec0">Hi {{ name }}, click the button below to reset your password. This link expires in 1 hour.</p>
  <div style="text-align:center;margin:24px 0">
    <a href="{{ reset_url }}" style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:14px 32px;border-radius:50px;text-decoration:none;font-weight:700">Reset Password →</a>
  </div>
  <p style="color:#718096;font-size:13px">If you didn't request this, you can safely ignore this email.</p>
</div>
</div></body></html>
"""
}

jinja_env = Environment(loader=BaseLoader())


def render_template(template_name: str, **kwargs) -> str:
    """Render an email template with given context."""
    template_str = TEMPLATES.get(template_name, "")
    kwargs.setdefault("app_url", settings.app_url)
    template = jinja_env.from_string(template_str)
    return template.render(**kwargs)


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
) -> bool:
    """Send an email via Gmail SMTP."""
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP not configured, skipping email send")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
    msg["To"] = to_email

    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except smtplib.SMTPException as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_welcome_email(to_email: str, name: str) -> bool:
    html = render_template("welcome", name=name)
    return await send_email(to_email, f"Welcome to {settings.app_name}! 🎉", html)


async def send_payment_confirmation(
    to_email: str, name: str, plan: str, amount: float,
    currency: str, expiry: str, transaction_id: str
) -> bool:
    html = render_template(
        "payment_confirmation", name=name, plan=plan,
        amount=amount, currency=currency, expiry=expiry,
        transaction_id=transaction_id
    )
    return await send_email(to_email, f"✅ Payment Confirmed — {settings.app_name}", html)


async def send_subscription_expiring(to_email: str, name: str, days: int) -> bool:
    html = render_template("subscription_expiring", name=name, days=days)
    return await send_email(to_email, f"⚠️ Your VPN subscription expires in {days} days", html)


async def send_password_reset(to_email: str, name: str, reset_token: str) -> bool:
    reset_url = f"{settings.app_url}/reset-password?token={reset_token}"
    html = render_template("password_reset", name=name, reset_url=reset_url)
    return await send_email(to_email, "Reset your MAMA CHOL VPN password", html)
