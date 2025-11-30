from src.worker.celery_app import celery
from src.core.config import settings
from src.core.database import get_db_sync
from src.domain.models import Project
from sqlalchemy import select
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
        
        # Execute browser automation workflow via Browser Use Cloud
        result = _execute_browser_workflow(
            project_id=project_id,
            instructions=project.system_prompt,
            cookies=project.auth_cookies or {},
            schema_guide=project.output_schema or {}
        )
        
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


def _execute_browser_workflow(project_id: str, instructions: str, cookies: dict, schema_guide: dict):
    """
    Execute the browser automation workflow using Browser Use Cloud SDK
    """
    from browser_use_sdk import BrowserUse

    # Generate unique session ID for this workflow
    session_id = str(uuid.uuid4())

    # Initialize Browser Use Cloud client
    client = BrowserUse(api_key=settings.browser_use_api_key)

    # Construct the task prompt with schema guide and blocking instructions
    task_prompt = (
        f"You are a CRM Agent. {instructions}\n"
        f"Output must strictly follow this schema: {schema_guide}\n"
        f"IMPORTANT: If you encounter a CAPTCHA, authentication required, "
        f"or any blocking situation, immediately STOP and return status: 'BLOCKED' "
        f"with details about what you need help with."
    )

    logger.info(f"Creating Browser Use Cloud task for project {project_id} with session {session_id}")

    # Create and execute the cloud task
    task = client.tasks.create_task(
        task=task_prompt,
        llm="browser-use-llm"
    )

    # Get live stream URL if available
    stream_url = getattr(task, 'live_url', None) or getattr(task, 'stream_url', None)

    # Update project with session info
    _update_project_session(project_id, session_id, stream_url)

    logger.info(f"Browser Use Cloud task created for project {project_id}")
    if stream_url:
        logger.info(f"Live stream URL: {stream_url}")

    # Wait for task completion
    result = task.complete()

    # Check if agent was blocked
    output = getattr(result, 'output', str(result))
    if 'BLOCKED' in str(output).upper():
        logger.info(f"Agent blocked for project {project_id}")
        _update_project_status(project_id, "BLOCKED", "Manual intervention required")
        result_data = {
            "session_id": session_id,
            "status": "BLOCKED",
            "stream_url": stream_url,
            "output": output,
            "blocked_at": datetime.utcnow().isoformat()
        }
        _update_project_result(project_id, result_data)
        return result_data

    logger.info(f"Browser workflow completed successfully for project {project_id}")

    result_data = {
        "session_id": session_id,
        "status": "COMPLETED",
        "stream_url": stream_url,
        "output": output,
        "completed_at": datetime.utcnow().isoformat()
    }
    _update_project_result(project_id, result_data)
    return result_data


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


def _update_project_session(project_id: str, session_id: str, stream_url: str = None):
    """Update project with active session ID and stream URL"""
    try:
        with get_db_sync() as db:
            result = db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()

            if project:
                project.active_session_id = session_id
                project.live_stream_url = stream_url
                db.commit()
                logger.info(f"Updated project {project_id} with session {session_id} and stream URL")

    except Exception as e:
        logger.error(f"Error updating project session: {e}")


def _update_project_result(project_id: str, result_data: dict):
    """Update project with the result from the last agent run"""
    try:
        with get_db_sync() as db:
            result = db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()

            if project:
                project.last_result = result_data
                project.last_run_at = datetime.utcnow()
                db.commit()
                logger.info(f"Updated project {project_id} with agent result")

    except Exception as e:
        logger.error(f"Error updating project result: {e}")


