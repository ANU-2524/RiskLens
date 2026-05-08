# RiskLens — Complete Setup Guide

## 🚀 Quick Start (Recommended)

### Step 1: Prerequisites

Ensure you have installed:
- **Docker Desktop** (includes Docker Compose)
- **Git**

Optional but recommended:
- **Claude API key** from https://console.anthropic.com/
- **Alpha Vantage API key** from https://www.alphavantage.co/support/#api-key

### Step 2: Clone and Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd RiskLens

# Copy environment template
cp .env.example .env

# Edit .env with your favorite editor
# Add your API keys (optional but enables full AI features):
# ANTHROPIC_API_KEY=sk-ant-...
# ALPHA_VANTAGE_API_KEY=your-key-here
```

### Step 3: Start the Full Stack

```bash
# Build and start all services
docker-compose up --build

# This will start:
# - PostgreSQL (port 5432)
# - Redis (port 6379)
# - FastAPI backend (port 8000)
# - Celery workers (background tasks)
# - React frontend (port 5173)
```

Wait for all services to be healthy (watch the logs).

### Step 4: Seed Demo Data

Open a **new terminal** and run:

```bash
# Seed the database with historical demo data
docker-compose exec backend python -m app.db.seed
```

This creates:
- 25+ tracked entities (companies, countries, sectors)
- 500+ historical signals demonstrating predictive capabilities
- Risk scores showing RiskLens flagging SVB, FTX, Evergrande before collapse
- 2 demo users (analyst and viewer roles)

### Step 5: Access RiskLens

Open your browser:

**Frontend:** http://localhost:5173

**Login credentials:**
- **Analyst:** `demo@RiskLens.ai` / `RiskLens2024` (full access)
- **Viewer:** `viewer@RiskLens.ai` / `viewer2024` (read-only)

**API Documentation:** http://localhost:8000/docs

---

## 🛠️ Manual Setup (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set up environment
cp ../.env.example .env
# Edit .env with your database URL and API keys

# Start PostgreSQL and Redis locally
# (Install via Homebrew, apt, or use Docker)

# Run migrations
alembic upgrade head

# Seed data
python -m app.db.seed

# Start backend
uvicorn app.main:app --reload --port 8000

# In separate terminals, start Celery:
celery -A app.workers.tasks worker --loglevel=info
celery -A app.workers.tasks beat --loglevel=info
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Frontend will be available at http://localhost:5173
```

---

## 🧪 Testing the Platform

### 1. Galaxy Map
- Navigate to the homepage
- You'll see a 3D star field with ~25 entities
- Stars are color-coded by risk (cyan = low, red = critical)
- Click any star to open the entity detail panel

### 2. Live Risk Feed
- Check the left sidebar for real-time alerts
- Alerts are sorted by recency
- Click any alert to view full entity details

### 3. Natural Language Query
- Use the search bar at the top
- Try: "What companies in Asia are at high risk?"
- Try: "Which crypto exchanges show elevated risk?"
- RiskLens will respond with AI-generated answers

### 4. Dashboard
- Navigate to Dashboard page
- View summary statistics
- See sector risk comparison charts
- Identify highest risk entities

### 5. Timeline Explorer
- Navigate to Timeline page
- Select an entity (e.g., "Silicon Valley Bank")
- View 30-day risk score history
- See how RiskLens flagged risk before collapse

### 6. PDF Reports
- Navigate to Reports page
- Select an entity
- Click "Generate PDF Report"
- Download professional audit-ready risk report

---

## 🔧 Development

### Backend Development

```bash
cd backend

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Lint code
ruff check .

# Type checking
mypy .

# Format code
ruff format .

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Run linter
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🚢 Production Deployment

### Option 1: Deploy to Railway (Recommended)

**Backend:**
1. Create new project on Railway
2. Add PostgreSQL and Redis services
3. Connect GitHub repo
4. Set root directory to `backend/`
5. Add environment variables from `.env.example`
6. Deploy
7. Run migrations: `alembic upgrade head`
8. Seed data: `python -m app.db.seed`

**Frontend:**
1. Deploy to Vercel
2. Connect GitHub repo
3. Set root directory to `frontend/`
4. Set build command: `npm run build`
5. Set output directory: `dist`
6. Add env var: `VITE_API_URL=<your-backend-url>`

### Option 2: Deploy to Render

Similar process to Railway. Use Render's managed PostgreSQL and Redis.

### Option 3: Deploy to AWS/GCP/Azure

Use managed services:
- **Database:** RDS PostgreSQL / Cloud SQL / Azure Database
- **Cache:** ElastiCache Redis / Memorystore / Azure Cache
- **Backend:** ECS / Cloud Run / App Service
- **Frontend:** S3 + CloudFront / Cloud Storage + CDN / Static Web Apps

---

## 🐛 Troubleshooting

### Docker Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs backend
docker-compose logs postgres

# Restart services
docker-compose restart

# Clean rebuild
docker-compose down -v
docker-compose up --build
```

**Port conflicts:**
```bash
# Check what's using ports
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Kill processes or change ports in docker-compose.yml
```

### Database Issues

**Migration errors:**
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres redis
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.db.seed
```

### Frontend Issues

**Build errors:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**API connection errors:**
- Check backend is running: http://localhost:8000/health
- Check CORS settings in `backend/app/core/config.py`
- Verify proxy settings in `frontend/vite.config.ts`

### Celery Issues

**Tasks not running:**
```bash
# Check Celery worker logs
docker-compose logs celery-worker

# Check Celery beat logs
docker-compose logs celery-beat

# Restart workers
docker-compose restart celery-worker celery-beat
```

---

## 📊 Performance Optimization

### Backend

- **Database:** Add indexes on frequently queried columns
- **Caching:** Redis TTLs are configured (5min for risk scores, 1min for alerts)
- **Rate Limiting:** 100 requests/minute per IP
- **Connection Pooling:** SQLAlchemy pool size = 10, max overflow = 20

### Frontend

- **Code Splitting:** Vite automatically splits routes
- **Image Optimization:** Use WebP format for images
- **Bundle Size:** Run `npm run build` and check dist/ size
- **Lighthouse Score:** Target 90+ (already optimized)

---

## 🔐 Security Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` in `.env` to a strong random string
- [ ] Use strong database passwords
- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Restrict CORS origins to your production domain
- [ ] Enable rate limiting on all public endpoints
- [ ] Set up database backups
- [ ] Enable Redis persistence
- [ ] Use environment-specific API keys
- [ ] Review and restrict database user permissions
- [ ] Enable logging and monitoring
- [ ] Set up error tracking (Sentry, etc.)

---

## 📚 Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **Three.js Docs:** https://threejs.org/docs/
- **Claude API Docs:** https://docs.anthropic.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Celery Docs:** https://docs.celeryq.dev/

---

## 🆘 Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs <service-name>`
2. Review this troubleshooting guide
3. Check GitHub Issues
4. Review the README.md for architecture details

---

**RiskLens** — Built for production, designed for impact.

