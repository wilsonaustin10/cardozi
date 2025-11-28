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
- **Project**: Main entity storing CRM project state, browser sessions, and authentication cookies
- Fields: `id`, `status`, `system_prompt`, `output_schema`, `auth_cookies`, `live_stream_url`, `active_session_id`

### Worker Tasks (`backend/src/worker/tasks.py`)
- `run_agent_workflow`: Executes browser automation using Browser Use SDK
- Handles cloud browser initialization, agent execution, and error states (BLOCKED for CAPTCHAs)

### API Layer (`backend/src/api/main.py`)
- FastAPI gateway for project management and task queuing
- Interfaces between frontend and Celery worker

## Deployment Strategy

### Railway (Backend)
- Uses same Docker image for both API and Worker services
- Service differentiation via `SERVICE_TYPE` environment variable
- API service: `SERVICE_TYPE=api`
- Worker service: `SERVICE_TYPE=worker`

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