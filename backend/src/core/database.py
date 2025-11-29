from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager
from .config import settings

# Convert postgres:// to postgresql+asyncpg:// if needed  
database_url = settings.database_url
async_database_url = database_url
if async_database_url.startswith("postgresql://"):
    async_database_url = async_database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create sync engine (for Celery workers)
sync_engine = create_engine(
    database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Create async engine
engine = create_async_engine(
    async_database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Create session factories
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
def get_db_sync():
    """Synchronous database session for Celery workers"""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


async def create_tables():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)