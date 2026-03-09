"""Application settings using pydantic-settings."""
from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional, List
import secrets


class Settings(BaseSettings):
    # Application
    app_name: str = "MAMA CHOL VPN"
    app_url: str = "https://mamachol.online"
    debug: bool = False
    version: str = "1.0.0"

    # Security
    secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/mamachol"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # CORS
    allowed_origins: List[str] = ["https://mamachol.online", "http://localhost:3000"]

    # bKash
    bkash_app_key: str = ""
    bkash_app_secret: str = ""
    bkash_username: str = ""
    bkash_password: str = ""
    bkash_base_url: str = "https://tokenized.pay.bka.sh/v1.2.0-beta"

    # Nagad
    nagad_merchant_id: str = ""
    nagad_merchant_private_key: str = ""
    nagad_base_url: str = "http://sandbox.mynagad.com:10080/remote-payment-gateway-1.0"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "MAMA CHOL VPN"

    # Telegram
    telegram_bot_token: str = ""
    telegram_admin_chat_id: str = ""

    # X-UI Panel
    xui_url: str = "http://localhost:54321"
    xui_username: str = "admin"
    xui_password: str = "admin"

    # Ollama AI
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # Exchange Rate
    exchange_rate_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
