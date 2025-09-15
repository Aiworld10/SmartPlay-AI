# async DB engine and session setup for FastAPI with SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from collections.abc import AsyncGenerator  # to type hint the async generator
from model.models import Base

import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables from .env file
load_dotenv()

# Retrieve database connection details from environment variables
DB_USER = os.getenv("DB_USER")
# URL encode special characters in password
RAW_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", ""))
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Construct the full database URL for the asyncpg driver
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# Create the async engine with pool pre-ping to handle stale connections
engine = create_async_engine(
    DATABASE_URL,
    echo=True,          # Set to False in production to reduce log verbosity
    future=True,        # Enable 2.0 style SQLAlchemy usage
    pool_pre_ping=True  # Checks connections are alive before using them
)
# Configure async sessionmaker: expire_on_commit=False keeps objects alive after commit
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
# Base class for declarative models, expose `__tablename__`
Base = Base
# Dependency to get async session (used with FastAPI depends, it use the only 1 engine instance per app for many requests)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that yields an SQLAlchemy AsyncSession.
    Ensures session is properly closed after use.
    """
    async with AsyncSessionLocal() as session:
        yield session
