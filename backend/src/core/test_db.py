"""
Test database functionality with SQLite for debugging
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, JSON, DateTime, func, select
import uuid
import asyncio

# Create SQLite async engine for testing
engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="INITIALIZING")
    system_prompt = Column(String)
    output_schema = Column(JSON)
    auth_cookies = Column(JSON)
    live_stream_url = Column(String)
    active_session_id = Column(String)
    created_at = Column(DateTime, server_default=func.now())

async def test_database():
    """Test database operations"""
    print("🔧 Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("🔧 Testing project creation...")
    async with AsyncSessionLocal() as session:
        project = Project(
            id=str(uuid.uuid4()),
            system_prompt="Test CRM agent",
            status="INITIALIZING"
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        print(f"✅ Project created: {project.id}")
        
        # Test query
        result = await session.execute(select(Project))
        projects = result.scalars().all()
        print(f"✅ Found {len(projects)} projects")
        
    await engine.dispose()
    print("✅ Database test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_database())