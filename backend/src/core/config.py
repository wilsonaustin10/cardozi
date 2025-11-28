from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local for local development only
project_root = Path(__file__).resolve().parent.parent.parent.parent  # backend/src/core -> cardozi/
env_path = project_root / ".env.local"
if env_path.exists():
    load_dotenv(env_path)

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # API Keys
    browser_use_api_key: str
    openai_api_key: str
    
    # App Config
    app_name: str = "Cardozi CRM Agent"
    debug: bool = False
    
    class Config:
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields like NEXT_PUBLIC_API_URL
        env_file = None  # Don't try to load .env files in production


settings = Settings()