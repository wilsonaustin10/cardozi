from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Cardozi CRM Agent API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}

@app.get("/test-config")
async def test_config():
    return {
        "app_name": settings.app_name,
        "database_host": settings.database_url.split("@")[1].split(":")[0] if "@" in settings.database_url else "unknown",
        "redis_configured": bool(settings.redis_url)
    }