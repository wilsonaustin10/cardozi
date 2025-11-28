Here is the updated **Cardozi** architectural design and build plan, refactored for a **Vercel + Railway** deployment strategy and a **"No-Docker Local"** development workflow.

---

# Project Cardozi: Cloud-Native Agent Architecture

## 1. Architectural Blueprint

This system adopts a **Hybrid Serverless/Container** model. We decouple the ephemeral frontend (Next.js on Vercel) from the stateful, long-running backend (Python on Railway).

### High-Level Diagram

```mermaid
graph TD
    subgraph "Vercel (Frontend)"
        User((User))
        NextJS[Next.js CRM]
        Iframe[Browser View Iframe]
        
        User -->|HTTPS| NextJS
        NextJS -->|User Auth| Iframe
    end

    subgraph "Railway (Backend Project)"
        LB[Load Balancer]
        
        subgraph "Service A: API Server"
            FastAPI[FastAPI Gateway]
            Auth[Auth & Project Mgr]
        end
        
        subgraph "Service B: Worker"
            Celery[Celery Worker]
            BrowserSDK[Browser Use SDK]
        end
        
        subgraph "Data Persistence"
            Postgres[(PostgreSQL DB)]
            Redis[(Redis Queue)]
        end
        
        NextJS -->|REST API| LB --> FastAPI
        FastAPI -->|Enqueue Task| Redis
        Redis -->|Consume Task| Celery
        Celery -->|Read/Write State| Postgres
        FastAPI -->|Read Project State| Postgres
    end

    subgraph "External Cloud"
        BrowserCloud[Browser Use Cloud Fleet]
        TargetWeb[Target Websites]
        
        Celery -->|Instruction| BrowserCloud
        BrowserCloud -.->|Stream URL| Iframe
        BrowserCloud -->|Scrape| TargetWeb
    end
```

---

## 2. Project Directory Structure (Monorepo)

We separate concerns at the root level to allow Vercel and Railway to detect their respective application contexts automatically.

```text
cardozi/
├── .env.local               # Local secrets (API Keys, DB URLs) - DO NOT COMMIT
├── .gitignore               # Ignore venv/, node_modules/, .env
│
├── frontend/                # Next.js Application -> Deploys to Vercel
│   ├── src/
│   ├── package.json
│   └── ...
│
└── backend/                 # Python Application -> Deploys to Railway
    ├── src/
    │   ├── __init__.py
    │   ├── api/             # HTTP Layer (FastAPI)
    │   │   └── main.py
    │   ├── core/            # Config & DB Connections
    │   │   └── config.py
    │   ├── domain/          # Database Models
    │   │   └── models.py
    │   └── worker/          # Logic Layer (Celery)
    │       ├── celery_app.py
    │       └── tasks.py
    │
    ├── Dockerfile           # Railway Build Instruction
    ├── start.sh             # Logic to toggle between API and Worker modes
    └── requirements.txt     # Python Dependencies
```

---

## 3. Detailed Build Plan

### Phase 0: Environment & Infrastructure Setup

**Objective:** configure the "Bare Metal" local environment and prepare the Cloud infrastructure.

**1. Cloud Database Setup (Dev & Prod):**
Since we are skipping local Docker, we need accessible databases.
*   **PostgreSQL:** Create a free project on **Neon.tech** or **Supabase**. Copy the connection string.
*   **Redis:** Create a free Redis instance on **Upstash** or **Railway**. Copy the URL.

**2. Local Configuration:**
Create `.env.local` in the root:
```ini
# Backend Secrets
BROWSER_USE_API_KEY="your_key_here"
OPENAI_API_KEY="your_key_here"
DATABASE_URL="postgres://user:pass@ep-xyz.neon.tech/cardozi?sslmode=require"
REDIS_URL="redis://default:pass@fly-xyz.upstash.io:6379"

# Frontend Secrets
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

**3. Python Setup:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi "uvicorn[standard]" sqlalchemy asyncpg pydantic-settings celery[redis] browser-use langchain-openai python-dotenv
pip freeze > requirements.txt
```

---

### Phase 1: The Deployment Configuration (Railway Prep)

**Objective:** Create the logic that allows Railway to build the image once but run it in two different modes (API vs. Worker).

**1. Create `backend/Dockerfile`:**
```dockerfile
FROM python:3.11-slim

# Optimization flags
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (needed for some browser-use/playwright internals)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Code
COPY . .

# Permissions
RUN chmod +x start.sh

# Default Entrypoint
CMD ["./start.sh"]
```

**2. Create `backend/start.sh`:**
```bash
#!/bin/bash

# Detect mode based on Railway Service Variable
if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "✅ Starting Celery Worker..."
    celery -A src.worker.celery_app worker --loglevel=info
else
    echo "✅ Starting FastAPI Server..."
    # Railway injects $PORT automatically
    uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
fi
```

---

### Phase 2: Core Application Logic

**Objective:** Implement the "Theory of Operation" (State Management + Browser Control).

**1. Database Connection (`backend/src/core/database.py`):**
Use `sqlalchemy.ext.asyncio` to ensure the API doesn't block while writing state.

**2. Define the Schema (`backend/src/domain/models.py`):**
```python
from sqlalchemy import Column, String, JSON, DateTime, func
from src.core.database import Base
import uuid

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="INITIALIZING") # INITIALIZING, IDLE, RUNNING, BLOCKED
    
    # The "Theory"
    system_prompt = Column(String)
    output_schema = Column(JSON)
    
    # The "Memory"
    auth_cookies = Column(JSON) 
    
    # The "View"
    live_stream_url = Column(String)
    active_session_id = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
```

**3. The Worker Logic (`backend/src/worker/tasks.py`):**
This handles the heavy lifting.

```python
from src.worker.celery_app import celery
from browser_use import Agent, Browser
import asyncio
import os

@celery.task(bind=True)
def run_agent_workflow(self, project_id, instructions, cookies, schema_guide):
    """
    Executes the agentic workflow on the cloud.
    """
    async def _execute():
        # 1. Initialize Cloud Browser with User Identity
        browser = Browser(
            use_cloud=True, 
            config={"cookies": cookies} 
        )
        
        # 2. Construct System Prompt (The "Theory")
        system = (
            f"You are a CRM Agent. Output must strictly follow: {schema_guide}. "
            f"If you encounter a CAPTCHA or cannot proceed, "
            f"STOP and return status: 'BLOCKED'."
        )

        agent = Agent(
            task=instructions,
            llm=os.getenv("LLM_MODEL", "gpt-4o"),
            browser=browser,
            system_prompt=system
        )

        # 3. Run & Handle Result
        history = await agent.run()
        result = history.final_result()
        
        if result.status == 'BLOCKED':
            # Save the session for human rescue
            update_db_status(project_id, "BLOCKED", url=browser.cloud_url)
            # DO NOT CLOSE BROWSER
        else:
            # Success
            save_result(project_id, result)
            await browser.close()

    asyncio.run(_execute())
```

---

### Phase 3: The "No-Docker" Local Dev Workflow

**Objective:** Run the system on your laptop without containers.

Since we aren't using `docker-compose`, you must run processes manually.

**Terminal 1: The API Server**
```bash
# In /backend
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2: The Worker**
```bash
# In /backend
source venv/bin/activate
celery -A src.worker.celery_app worker --loglevel=info
```

**Terminal 3: The Frontend**
```bash
# In /frontend
npm run dev
```

*Verification:* Visit `localhost:3000`. Create a project. Check Terminal 1 logs for the request, Terminal 2 logs for the execution.

---

### Phase 4: Production Deployment (Railway & Vercel)

**Objective:** Push to Git and have the system go live.

**1. Railway (Backend)**
1.  **New Project:** Select your GitHub Repo.
2.  **Add Resources:** Add PostgreSQL and Redis plugins within Railway.
3.  **Deploy Service A (API):**
    *   Settings → Root Directory: `backend`
    *   Variables: `SERVICE_TYPE=api`, `BROWSER_USE_API_KEY`, `DATABASE_URL` (use Railway's variable `${{PostgreSQL.DATABASE_URL}}`).
4.  **Deploy Service B (Worker):**
    *   Click "New Service" → Select same GitHub Repo.
    *   Settings → Root Directory: `backend`
    *   Variables: `SERVICE_TYPE=worker`, `BROWSER_USE_API_KEY`, `DATABASE_URL`, `REDIS_URL`.

**2. Vercel (Frontend)**
1.  **New Project:** Select GitHub Repo.
2.  **Settings:**
    *   Root Directory: `frontend`
    *   Env Variables: `NEXT_PUBLIC_API_URL` -> (Your Railway API URL, e.g., `https://api-production.up.railway.app`).
3.  **Deploy.**

---

## 4. Quality Control & Checkpoints

1.  **The "Idle" Check:**
    *   *Test:* Deploy to Railway. If `SERVICE_TYPE` logic is wrong, the worker might crash or try to bind to a port and fail.
    *   *Validation:* Check Railway logs. "Service A" should say `Uvicorn running on...`. "Service B" should say `Celery@... ready`.

2.  **The "Persistence" Check:**
    *   *Test:* Run a manual session locally (`localhost:3000`), log into a site, and capture cookies.
    *   *Validation:* Check your Neon/Supabase DB table `projects`. The `auth_cookies` column should not be empty.
    *   *Test:* Trigger an agent run.
    *   *Validation:* The agent (running on Railway) should successfully use those cookies to access the site without login.

3.  **The "Rescue" Check:**
    *   *Test:* Force the agent to fail (give it a bad selector).
    *   *Validation:* Project status changes to `BLOCKED`. Frontend shows "Resume" button. Clicking resume re-opens the **exact same session**.