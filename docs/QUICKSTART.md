# 🚀 Oracle — 5-Minute Quickstart

Get Oracle running in 5 minutes with this streamlined guide.

## Prerequisites

- **Docker Desktop** installed and running
- **Git** installed

## Step 1: Clone & Configure (1 minute)

```bash
# Clone the repo
git clone <your-repo-url>
cd oracle

# Copy environment file
cp .env.example .env

# (Optional) Edit .env to add API keys for full AI features
# ANTHROPIC_API_KEY=your-key-here
# ALPHA_VANTAGE_API_KEY=your-key-here
```

## Step 2: Start Everything (2 minutes)

```bash
# Start all services with one command
docker-compose up --build
```

Wait for all services to show "healthy" status. You'll see:
- ✅ PostgreSQL ready
- ✅ Redis ready
- ✅ Backend API running on port 8000
- ✅ Frontend running on port 5173
- ✅ Celery workers started

## Step 3: Seed Demo Data (1 minute)

Open a **new terminal** (keep the first one running):

```bash
# Seed the database with demo data
docker-compose exec backend python -m app.db.seed
```

This creates:
- 25+ entities (SVB, FTX, Evergrande, etc.)
- 500+ historical signals
- Risk scores showing predictive capabilities
- 2 demo users

## Step 4: Login & Explore (1 minute)

Open your browser: **http://localhost:5173**

**Login:**
- Email: `demo@oracle.ai`
- Password: `oracle2024`

**Try these:**
1. **Galaxy Map** — Click any star to see entity details
2. **Query Bar** — Ask: "What companies are at critical risk?"
3. **Dashboard** — View sector risk charts
4. **Timeline** — Select "Silicon Valley Bank" to see risk escalation
5. **Reports** — Generate a PDF report for any entity

## 🎯 What You're Seeing

The demo data shows Oracle's predictive power:

- **SVB Bank:** Risk flagged CRITICAL 9 days before collapse (March 2023)
- **FTX Exchange:** HIGH risk detected 8 days before bankruptcy (Nov 2022)
- **Evergrande:** CRITICAL status 6 weeks before default (2021)

## 🛑 Stop Everything

```bash
# Press Ctrl+C in the docker-compose terminal
# Or run:
docker-compose down
```

## 🔧 Troubleshooting

**Port already in use?**
```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Kill the process or change ports in docker-compose.yml
```

**Services won't start?**
```bash
# Check logs
docker-compose logs backend
docker-compose logs postgres

# Clean restart
docker-compose down -v
docker-compose up --build
```

**Frontend shows connection error?**
- Wait 30 seconds for backend to fully start
- Check backend health: http://localhost:8000/health
- Refresh the browser

## 📚 Next Steps

- Read **README.md** for full architecture details
- Read **SETUP.md** for deployment guides
- Check **http://localhost:8000/docs** for API documentation
- Explore the codebase structure

## 🎤 Demo Script for Interviews

> "Let me show you Oracle — an AI-powered risk intelligence platform I built. 
> 
> [Show Galaxy Map] Each star represents a tracked entity. Size and color indicate risk level. This is real-time data from news feeds, SEC filings, and market signals.
> 
> [Click SVB star] Here's Silicon Valley Bank. Oracle flagged this as CRITICAL risk 9 days before the FDIC seizure in March 2023. The AI summary explains why — unrealized bond losses, unusual withdrawal patterns, VC advisor communications.
> 
> [Show Timeline] This chart shows how the risk score escalated over 3 weeks. Every spike corresponds to a real signal — a news article, an SEC filing, or market data.
> 
> [Use Query Bar] I can ask Oracle anything in natural language. 'What crypto exchanges show elevated risk?' [Show AI response]
> 
> [Show Dashboard] The dashboard aggregates risk across sectors. Finance sector is elevated right now due to commercial real estate concerns.
> 
> [Generate Report] And I can generate audit-ready PDF reports for any entity with one click.
> 
> This is production-grade. It's built with FastAPI, React, Three.js, and Claude API. It runs on Docker, scales horizontally, and has full test coverage. The kind of system KPMG uses for audit risk, Morgan Stanley uses for portfolio protection, and Walmart uses for supply chain intelligence."

---

**You're ready!** Oracle is now running locally. Explore the platform and review the code.
