"""FastAPI main application for MAMA CHOL VPN."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from backend.config.settings import settings
from backend.models.database import create_tables
from backend.api import auth, user, vpn, payment, admin

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    try:
        create_tables()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-Powered Multi-Mode VPN Service API",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{duration:.3f}s"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later.", "code": "INTERNAL_ERROR"}
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/api/v1/user", tags=["User"])
app.include_router(vpn.router, prefix="/api/v1/vpn", tags=["VPN"])
app.include_router(payment.router, prefix="/api/v1/payment", tags=["Payment"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.version, "service": settings.app_name}


@app.get("/api/v1/chat", tags=["AI"])
@app.post("/api/v1/chat", tags=["AI"])
async def ai_chat(request: Request):
    """AI chatbot endpoint."""
    from backend.services.ai_chatbot import chatbot
    body = await request.json()
    message = body.get("message", "")
    lang = body.get("lang", "en")
    history = body.get("history", [])

    if not message or len(message) > 1000:
        return JSONResponse(status_code=400, content={"detail": "Invalid message"})

    reply = await chatbot.chat(message, lang=lang, history=history)
    return {"reply": reply, "lang": lang}


@app.get("/api/v1/sub/{token}", tags=["VPN"])
async def subscription_link(token: str):
    """Return subscription URL content (all VPN links in one)."""
    from sqlalchemy.orm import Session
    from backend.models.database import get_db, VPNConfig
    import base64

    db = next(get_db())
    config = db.query(VPNConfig).filter(VPNConfig.subscription_token == token).first()
    if not config:
        return JSONResponse(status_code=404, content={"detail": "Subscription not found"})

    links = []
    for link in [config.vless_reality_link, config.vmess_ws_link,
                 config.trojan_grpc_link, config.shadowsocks_link]:
        if link:
            links.append(link)

    content = base64.b64encode("\n".join(links).encode()).decode()
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content, media_type="text/plain")
