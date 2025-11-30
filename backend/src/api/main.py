from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import get_db, create_tables
from src.core.config import settings
from src.domain.models import Project
from src.worker.tasks import run_agent_workflow
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

app = FastAPI(title=settings.app_name, debug=settings.debug)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://cardozi.vercel.app",  # Production frontend (when deployed)
        "https://*.vercel.app"  # Allow any Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectCreate(BaseModel):
    system_prompt: str
    output_schema: Optional[Dict[Any, Any]] = None


class ProjectResponse(BaseModel):
    id: str
    status: str
    system_prompt: Optional[str] = None
    output_schema: Optional[Dict[Any, Any]] = None
    auth_cookies: Optional[Dict[Any, Any]] = None
    live_stream_url: Optional[str] = None
    active_session_id: Optional[str] = None
    last_result: Optional[Dict[Any, Any]] = None
    last_run_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@app.on_event("startup")
async def startup_event():
    """Create tables on startup"""
    await create_tables()


@app.get("/")
async def root():
    return {"message": "Cardozi CRM Agent API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}


@app.post("/projects/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Create a new CRM project"""
    db_project = Project(
        id=str(uuid.uuid4()),
        system_prompt=project.system_prompt,
        output_schema=project.output_schema,
        status="INITIALIZING"
    )
    
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    
    return ProjectResponse(
        id=db_project.id,
        status=db_project.status,
        system_prompt=db_project.system_prompt,
        output_schema=db_project.output_schema,
        auth_cookies=db_project.auth_cookies,
        live_stream_url=db_project.live_stream_url,
        active_session_id=db_project.active_session_id,
        last_result=db_project.last_result,
        last_run_at=db_project.last_run_at,
        created_at=db_project.created_at,
        updated_at=db_project.updated_at
    )


@app.get("/projects/", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all projects"""
    result = await db.execute(select(Project))
    projects = result.scalars().all()
    
    return [
        ProjectResponse(
            id=project.id,
            status=project.status,
            system_prompt=project.system_prompt,
            output_schema=project.output_schema,
            auth_cookies=project.auth_cookies,
            live_stream_url=project.live_stream_url,
            active_session_id=project.active_session_id,
            last_result=project.last_result,
            last_run_at=project.last_run_at,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        for project in projects
    ]


@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
        id=project.id,
        status=project.status,
        system_prompt=project.system_prompt,
        output_schema=project.output_schema,
        auth_cookies=project.auth_cookies,
        live_stream_url=project.live_stream_url,
        active_session_id=project.active_session_id,
        last_result=project.last_result,
        last_run_at=project.last_run_at,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@app.post("/projects/{project_id}/run")
async def run_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Run the agent workflow for a project"""
    return await start_project(project_id, db)


@app.post("/projects/{project_id}/start")
async def start_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Start a project's agent workflow"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status == "RUNNING":
        raise HTTPException(status_code=400, detail="Project is already running")
    
    # Try to start the agent workflow with Celery worker
    try:
        task = run_agent_workflow.delay(project_id)
        return {
            "message": "Project started with Browser Use agent workflow",
            "project_id": project_id,
            "task_id": task.id
        }
    except Exception as e:
        # If Celery/Redis is not available or no workers, run simulation
        import asyncio
        from datetime import datetime
        
        # Update status to RUNNING immediately
        project.status = "RUNNING"
        await db.commit()
        
        # Simulate agent workflow with a delay
        async def simulate_workflow():
            await asyncio.sleep(5)  # Simulate 5 seconds of work
            # Refresh project from database
            async with db.begin():
                result = await db.execute(select(Project).where(Project.id == project_id))
                proj = result.scalar_one_or_none()
                if proj:
                    proj.status = "IDLE"
                    proj.active_session_id = "simulated-session-" + str(int(datetime.utcnow().timestamp()))
        
        # Run simulation in background
        asyncio.create_task(simulate_workflow())
        
        return {
            "message": "Project started in simulation mode (no Celery worker available)",
            "project_id": project_id,
            "mode": "simulation",
            "reason": str(e)
        }


@app.post("/projects/{project_id}/stop")
async def stop_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Stop a project's agent workflow"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update project status to IDLE (stopping the workflow)
    project.status = "IDLE"
    project.active_session_id = None
    project.live_stream_url = None
    await db.commit()
    
    return {
        "message": "Project stopped",
        "project_id": project_id
    }


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted", "project_id": project_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)