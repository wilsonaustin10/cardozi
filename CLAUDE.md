# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cardozi is a cloud-native agent architecture that combines a Next.js frontend (deployed on Vercel) with a Python backend (deployed on Railway). The system uses Browser Use SDK to automate web interactions through AI agents for CRM operations.

## Architecture

This is a monorepo with two main applications:

- `frontend/` - Next.js CRM interface deployed to Vercel
- `backend/` - Python FastAPI + Celery worker system deployed to Railway

The backend uses a hybrid serverless/container model with:
- **API Service**: FastAPI gateway handling HTTP requests
- **Worker Service**: Celery workers executing browser automation tasks
- **Data Layer**: PostgreSQL (via Neon/Supabase) and Redis (via Upstash/Railway)

## Development Environment Setup

### Prerequisites
```bash
# Backend Python environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi "uvicorn[standard]" sqlalchemy asyncpg pydantic-settings celery[redis] browser-use langchain-openai python-dotenv
```

### Local Development Commands

**Start the API server:**
```bash
cd backend
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

**Start the Celery worker:**
```bash
cd backend
source venv/bin/activate
celery -A src.worker.celery_app worker --loglevel=info
```

**Start the frontend:**
```bash
cd frontend
npm run dev
```

**Frontend development commands:**
```bash
# Build production version
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

**Backend testing:**
```bash
cd backend
source venv/bin/activate
# Install dependencies
pip install -r requirements.txt

# Test database connection
python src/core/test_db.py
```

### Environment Configuration

Create `.env.local` in the root directory:
```ini
# Backend Secrets
BROWSER_USE_API_KEY="your_key_here"
OPENAI_API_KEY="your_key_here"
DATABASE_URL="postgres://user:pass@ep-xyz.neon.tech/cardozi?sslmode=require"
REDIS_URL="redis://default:pass@fly-xyz.upstash.io:6379"

# Frontend Secrets
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

## Core Components

### Database Models (`backend/src/domain/models.py`)
- **Project**: Main entity with status-driven workflow
  - States: `INITIALIZING`, `IDLE`, `RUNNING`, `BLOCKED` 
  - Configuration: `system_prompt`, `output_schema` (AI agent settings)
  - Session data: `auth_cookies`, `live_stream_url`, `active_session_id`
  - Timestamps: `created_at`, `updated_at`

### Worker Tasks (`backend/src/worker/tasks.py`)
- `run_agent_workflow`: Core Celery task for browser automation
- Uses Browser Use SDK with async workflow execution
- Handles project status transitions and error recovery
- Supports session persistence for blocked states

### API Layer (`backend/src/api/main.py`)
- FastAPI with CORS for localhost and Vercel deployment
- Project CRUD operations with database integration
- Task queuing interface to Celery workers
- Startup event creates database tables

## Deployment Strategy

### Railway (Backend)
- Single Dockerfile builds both API and Worker services
- Service differentiation via `SERVICE_TYPE` environment variable and start commands:
  - API service: Default `bash start.sh` (no SERVICE_TYPE)
  - Worker service: `SERVICE_TYPE=worker bash start.sh`
- Configuration files: `railway.toml` (API) and `railway-worker.toml` (Worker)
- Chrome browser dependencies included for Browser Use automation

### Vercel (Frontend)
- Automatic deployment from `frontend/` directory
- Configured with Railway API URL as `NEXT_PUBLIC_API_URL`

## Key Technical Patterns

### State Management
Projects have four states: `INITIALIZING`, `IDLE`, `RUNNING`, `BLOCKED`
- `BLOCKED` state preserves browser sessions for human intervention
- Cookie persistence enables authenticated session resumption

### Browser Session Handling
- Uses Browser Use Cloud for scalable browser automation
- Live stream URLs provided for real-time monitoring
- Session persistence across agent failures

### Error Recovery
- CAPTCHA and blocking scenarios transition to `BLOCKED` state
- Browser sessions remain open for manual completion
- Resume functionality restores exact session state

## Development Workflow

### Adding New Features
1. **Frontend**: Components use Radix UI + Tailwind CSS patterns
2. **Backend**: Follow FastAPI router patterns and async/await
3. **Database**: Use SQLAlchemy models with UUID primary keys
4. **Tasks**: Implement as Celery tasks with proper status management

### Debugging
- API logs: Check Railway deployment logs for FastAPI service
- Worker logs: Check Railway deployment logs for Worker service  
- Frontend logs: Browser console and Vercel function logs
- Database: Use `python src/core/test_db.py` for connection testing

### Common Issues
- **Celery worker not found**: Ensure Worker service is deployed and Redis is accessible
- **CORS errors**: Verify frontend URL is in CORS origins list
- **Database connection**: Check DATABASE_URL format and SSL requirements
- **Browser automation fails**: Verify BROWSER_USE_API_KEY and Chrome dependencies