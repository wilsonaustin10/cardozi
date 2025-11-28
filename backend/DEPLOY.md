# Railway Deployment Guide

## Architecture

This backend deploys to Railway as two separate services using the same Docker image:

1. **API Service** - Handles HTTP requests (FastAPI)
2. **Worker Service** - Processes background tasks (Celery)

## Deployment Steps

### 1. Create Railway Project
```bash
railway login
railway init
```

### 2. Add Required Services

**PostgreSQL & Redis:**
- Add PostgreSQL plugin in Railway dashboard
- Add Redis plugin in Railway dashboard

### 3. Deploy API Service

**Service A (API Server):**
- Root Directory: `backend`
- Environment Variables:
  - `SERVICE_TYPE=api`
  - `DATABASE_URL=${{PostgreSQL.DATABASE_URL}}`
  - `REDIS_URL=${{Redis.REDIS_URL}}`
  - `BROWSER_USE_API_KEY=<your_key>`
  - `OPENAI_API_KEY=<your_key>`

### 4. Deploy Worker Service

**Service B (Worker):**
- Create new service from same GitHub repo
- Root Directory: `backend`
- Environment Variables:
  - `SERVICE_TYPE=worker`
  - `DATABASE_URL=${{PostgreSQL.DATABASE_URL}}`
  - `REDIS_URL=${{Redis.REDIS_URL}}`
  - `BROWSER_USE_API_KEY=<your_key>`
  - `OPENAI_API_KEY=<your_key>`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SERVICE_TYPE` | Yes | `api` or `worker` |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `BROWSER_USE_API_KEY` | Yes | Browser Use Cloud API key |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `PORT` | No | Auto-injected by Railway for API service |

## Health Checks

- **API Service:** `GET /health`
- **Worker Service:** Check Railway logs for "Celery@... ready"