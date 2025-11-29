from src.worker.celery_app import celery
from src.core.config import settings
from src.core.database import get_db_sync
from src.domain.models import Project
from sqlalchemy import select
import asyncio
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def run_agent_workflow(self, project_id: str):
    """
    Execute the agentic workflow using Browser Use SDK
    """
    logger.info(f"Starting agent workflow for project {project_id}")
    
    try:
        # Update project status to RUNNING
        _update_project_status(project_id, "RUNNING", "Agent workflow started")
        
        # Get project details from database
        project = _get_project(project_id)
        if not project:
            raise Exception(f"Project {project_id} not found")
        
        # Execute browser automation workflow
        result = asyncio.run(_execute_browser_workflow(
            project_id=project_id,
            instructions=project.system_prompt,
            cookies=project.auth_cookies or {},
            schema_guide=project.output_schema or {}
        ))
        
        # Update project status to IDLE when completed
        _update_project_status(project_id, "IDLE", "Agent workflow completed successfully")
        
        logger.info(f"Agent workflow completed for project {project_id}")
        return {
            "status": "completed",
            "project_id": project_id,
            "result": result,
            "message": "Agent workflow executed successfully"
        }
        
    except Exception as exc:
        logger.error(f"Agent workflow failed for project {project_id}: {exc}")
        # Update project status to BLOCKED on failure
        _update_project_status(project_id, "BLOCKED", f"Error: {str(exc)}")
        
        if self.request.retries < 3:
            self.retry(countdown=60, max_retries=3, exc=exc)
        else:
            return {
                "status": "failed",
                "project_id": project_id,
                "error": str(exc)
            }


@celery.task
def test_task(message: str):
    """Simple test task to verify Celery is working"""
    return f"Test task completed: {message}"


async def _execute_browser_workflow(project_id: str, instructions: str, cookies: dict, schema_guide: dict):
    """
    Execute the actual browser automation workflow using Browser Use SDK
    """
    try:
        from browser_use import Agent, Browser, BrowserConfig
        from langchain_openai import ChatOpenAI
        
        # Initialize the LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            openai_api_key=settings.openai_api_key,
            temperature=0
        )
        
        # Generate unique session ID for this workflow
        session_id = str(uuid.uuid4())
        
        # Update project with session info
        _update_project_session(project_id, session_id)
        
        # Configure browser for headless operation with live streaming
        browser_config = BrowserConfig(
            headless=False,  # Set to False to enable live streaming
            disable_security=True,
            extra_chromium_args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--remote-debugging-port=9222'  # Enable remote debugging for streaming
            ]
        )
        
        # Initialize browser and agent
        browser = Browser(config=browser_config)
        agent = Agent(
            task=instructions,
            llm=llm,
            browser=browser,
            use_vision=True
        )
        
        # Set cookies if provided
        if cookies:
            await browser.set_cookies(cookies)
        
        logger.info(f"Starting browser agent for project {project_id} with session {session_id}")
        
        # Execute the agent workflow
        result = await agent.run()
        
        # Clean up browser
        await browser.close()
        
        logger.info(f"Browser workflow completed for project {project_id}")
        
        return {
            "session_id": session_id,
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except ImportError:
        logger.warning("Browser Use SDK not available, running simulation mode")
        # Fallback to simulation for development
        await asyncio.sleep(10)  # Simulate work
        return {
            "session_id": str(uuid.uuid4()),
            "result": "Simulated browser workflow completed - Browser Use SDK not available",
            "completed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Browser workflow error for project {project_id}: {e}")
        raise


def _get_project(project_id: str) -> Project:
    """Get project from database synchronously"""
    try:
        with get_db_sync() as db:
            result = db.execute(select(Project).where(Project.id == project_id))
            return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}")
        return None


def _update_project_status(project_id: str, status: str, message: str = None):
    """Update project status in database synchronously"""
    try:
        with get_db_sync() as db:
            result = db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            
            if project:
                project.status = status
                # You could add a status_message field to track messages
                db.commit()
                logger.info(f"Updated project {project_id} status to {status}")
            else:
                logger.error(f"Project {project_id} not found for status update")
                
    except Exception as e:
        logger.error(f"Error updating project status: {e}")


def _update_project_session(project_id: str, session_id: str):
    """Update project with active session ID"""
    try:
        with get_db_sync() as db:
            result = db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            
            if project:
                project.active_session_id = session_id
                # Generate live stream URL (this would be your actual streaming endpoint)
                project.live_stream_url = f"ws://localhost:9222/devtools/browser/{session_id}"
                db.commit()
                logger.info(f"Updated project {project_id} with session {session_id}")
                
    except Exception as e:
        logger.error(f"Error updating project session: {e}")