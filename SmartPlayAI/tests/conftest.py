# conftest.py a global configuration file for pytest
# Configuration file for pytest to setup test database and client
# every function will use a fresh database session and a TestClient to interact with the FastAPI app, it will override the get_db dependency to use the test database session instead of the production one

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from model.models import Base
from model.database import get_session as get_db

# Use SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for tests, setting up the connection to a test database
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True
)

# Create session factory, binding connection to the engine so each request need this session
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Fixture to setup and drop tables before and after tests


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

    # Clean up: drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# this apply to every test function that uses the client fixture


@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient that uses the test database."""

    # get the db session
    async def db_session_yield():
        yield db_session

    # use the test db session in the app for testing
    app.dependency_overrides[get_db] = db_session_yield

    # Create TestClient
    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


# Configure asyncio event loop for pytest: the scheduler and traffic controller for async tasks for the whole session
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
