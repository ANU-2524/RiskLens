# Port Configuration

## Current Port Setup

Oracle is configured to run on the following ports:

- **Frontend:** http://localhost:5155 (React/Vite)
- **Backend API:** http://localhost:8000 (FastAPI)
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

## What Changed

The frontend port has been changed from the default **5173** to **5155**.

## Files Updated

1. ✅ `docker-compose.yml` - Frontend port mapping changed to `5155:5173`
2. ✅ `backend/app/core/config.py` - CORS origins updated to include `http://localhost:5155`
3. ✅ `.env.example` - CORS_ORIGINS updated
4. ✅ `docker-compose.yml` - Backend environment CORS_ORIGINS updated

## How to Run

```bash
# 1. Configure environment
cp .env.example .env

# 2. Start all services
docker-compose up --build

# 3. Seed data (in new terminal)
docker-compose exec backend python -m app.db.seed

# 4. Access the application
# Frontend: http://localhost:5155
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Login Credentials

- **Analyst:** demo@oracle.ai / oracle2024
- **Viewer:** viewer@oracle.ai / viewer2024

## Verify Everything Works

1. Frontend loads: http://localhost:5155
2. Backend health: http://localhost:8000/health
3. API docs: http://localhost:8000/docs

## Changing Ports (If Needed)

If you need to change ports in the future:

### Frontend Port

Edit `docker-compose.yml`:
```yaml
frontend:
  ports:
    - "YOUR_PORT:5173"  # Change YOUR_PORT to desired port
```

### Backend Port

Edit `docker-compose.yml`:
```yaml
backend:
  ports:
    - "YOUR_PORT:8000"  # Change YOUR_PORT to desired port
```

Then update CORS in `backend/app/core/config.py` and `.env.example`.

## Troubleshooting

**Port already in use:**
```bash
# Check what's using port 5155
lsof -i :5155  # Mac/Linux
netstat -ano | findstr :5155  # Windows

# Kill the process or change the port
```

**CORS errors:**
- Make sure CORS_ORIGINS in `.env` includes your frontend URL
- Restart backend after changing CORS settings
