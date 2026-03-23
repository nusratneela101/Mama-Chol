"""Pytest fixtures for MAMA CHOL VPN test suite."""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.main import app
from backend.models.database import Base, get_db, User
from backend.utils.encryption import hash_password, create_access_token, create_refresh_token
from backend.utils.helpers import generate_referral_code

# ---------------------------------------------------------------------------
# In-memory SQLite database for tests
# ---------------------------------------------------------------------------
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Truncate all tables between tests."""
    yield
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="session")
def client(setup_test_db):
    """Return a FastAPI TestClient with the test database and mocked email."""
    app.dependency_overrides[get_db] = override_get_db
    # Patch at the import location used by each module
    with patch("backend.api.auth.send_welcome_email", new_callable=AsyncMock), \
         patch("backend.services.email_service.send_password_reset", new_callable=AsyncMock), \
         patch("backend.api.payment.send_payment_confirmation", new_callable=AsyncMock):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    """Return a raw DB session for direct model manipulation."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def make_user(db, email="user@example.com", password="password123",
              full_name="Test User", is_admin=False, is_active=True):
    """Create and persist a User instance."""
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        referral_code=generate_referral_code(),
        is_admin=is_admin,
        is_active=is_active,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def normal_user(db):
    """A regular (non-admin) user."""
    return make_user(db)


@pytest.fixture()
def admin_user(db):
    """An admin user."""
    return make_user(db, email="admin@example.com", is_admin=True)


@pytest.fixture()
def user_token(normal_user):
    """JWT access token for normal_user."""
    return create_access_token({"sub": normal_user.id})


@pytest.fixture()
def admin_token(admin_user):
    """JWT access token for admin_user."""
    return create_access_token({"sub": admin_user.id})


@pytest.fixture()
def auth_headers(user_token):
    """Authorization headers for normal user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture()
def admin_headers(admin_token):
    """Authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}



# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    """Return a raw DB session for direct model manipulation."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def make_user(db, email="user@example.com", password="password123",
              full_name="Test User", is_admin=False, is_active=True):
    """Create and persist a User instance."""
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        referral_code=generate_referral_code(),
        is_admin=is_admin,
        is_active=is_active,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def normal_user(db):
    """A regular (non-admin) user."""
    return make_user(db)


@pytest.fixture()
def admin_user(db):
    """An admin user."""
    return make_user(db, email="admin@example.com", is_admin=True)


@pytest.fixture()
def user_token(normal_user):
    """JWT access token for normal_user."""
    return create_access_token({"sub": normal_user.id})


@pytest.fixture()
def admin_token(admin_user):
    """JWT access token for admin_user."""
    return create_access_token({"sub": admin_user.id})


@pytest.fixture()
def auth_headers(user_token):
    """Authorization headers for normal user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture()
def admin_headers(admin_token):
    """Authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
