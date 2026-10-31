from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


# The hosted database drops idle connections, so test each one before use
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=15,
    max_overflow=5,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# For independent read-only queries run in parallel: same pool, but no BEGIN / ROLLBACK
# round trip around each statement.
ReadOnlySession = async_sessionmaker(
    bind=engine.execution_options(isolation_level="AUTOCOMMIT"),
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass
