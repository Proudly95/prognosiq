import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401 - registers models on Base.metadata
from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app

# Single source of truth: whatever settings already uses for tests.
TEST_DB_URL = str(settings.database_url_test)

engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(bind=engine)


def _admin_url() -> str:
    """Same server + credentials, but pointed at the default 'prognosiq' DB."""
    url = make_url(TEST_DB_URL).set(database="prognosiq")
    return str(url)


def _ensure_test_db() -> None:
    """Create the test DB if missing. Idempotent — safe to run every time."""
    try:
        probe = sa.create_engine(TEST_DB_URL)
        with probe.connect():
            pass
        probe.dispose()
        return  # DB exists — nothing to do

    except OperationalError as exc:
        probe.dispose()
        if "does not exist" not in str(exc):
            raise  # server down / bad password / wrong port — fail loudly

    # DB is missing -> create it. CREATE DATABASE cannot run inside a
    # transaction, so the admin connection MUST use AUTOCOMMIT isolation.
    admin = sa.create_engine(_admin_url(), isolation_level="AUTOCOMMIT")
    target = make_url(TEST_DB_URL).database  # DB name derived, not hardcoded
    owner = make_url(TEST_DB_URL).username  # owner derived, not hardcoded
    with admin.connect() as conn:
        conn.execute(sa.text(f'CREATE DATABASE "{target}" OWNER "{owner}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    _ensure_test_db()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_database():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture()
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
