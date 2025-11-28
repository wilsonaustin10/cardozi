from sqlalchemy import Column, String, JSON, DateTime, func
from src.core.database import Base
import uuid


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="INITIALIZING")  # INITIALIZING, IDLE, RUNNING, BLOCKED
    
    # The "Theory" - AI Agent Configuration
    system_prompt = Column(String)
    output_schema = Column(JSON)
    
    # The "Memory" - Authentication & Session Data
    auth_cookies = Column(JSON)
    
    # The "View" - Browser Session Info
    live_stream_url = Column(String)
    active_session_id = Column(String)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())