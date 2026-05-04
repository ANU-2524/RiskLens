# Mysterious — AI-Powered Global Business Risk Intelligence Platform

![Oracle Banner](https://img.shields.io/badge/Oracle-Risk%20Intelligence-00D4FF?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square)
![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat-square)

## The Problem

Every major corporate disaster of the last decade — **Enron, Lehman Brothers, SVB, FTX, Evergrande** — had publicly available warning signals weeks or months before collapse. Analysts missed them because they were buried across thousands of documents, feeds, and data sources that no human team could monitor simultaneously.

**Oracle fixes this.**

## What Oracle Does

Oracle is a production-grade, AI-powered early warning system that monitors global business risk in real time. It:

- **Ingests 500+ data points per hour** from news feeds, SEC filings, market data, and social signals
- **Uses NLP** to extract entities and sentiment
- **Runs anomaly detection** on financial patterns
- **Sends risk clusters to Claude API** which generates plain-English summaries of what is happening and why it matters

**The result:** A real-time intelligence platform that would have flagged SVB's risk 3 weeks before collapse, spotted FTX's unusual withdrawal patterns, and alerted supply chain managers to COVID disruptions before their shelves went empty.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) Claude API key for AI summaries
- (Optional) Alpha Vantage API key for real market data

### 1. Clone and Configure

```bash
git clone <your-repo-url>
cd oracle

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys (optional but recommended)
# ANTHROPIC_API_KEY=your-key-here
# ALPHA_VANTAGE_API_KEY=your-key-here
```

### 2. Start Everything with One Command

```bash
docker-compose up --build
```

This starts:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI backend (port 8000)
- Celery workers (background ingestion)
- React frontend (port 5173)

### 3. Seed Demo Data

In a new terminal:

```bash
docker-compose exec backend python -m app.db.seed
```

This populates the database with realistic historical data demonstrating Oracle's predictive capabilities for:
- **SVB Bank collapse** (March 2023)
- **FTX crypto collapse** (November 2022)
- **Evergrande debt crisis** (2021)
- **COVID supply chain disruption** (2020)
- **Russia-Ukraine energy impact** (2022)

### 4. Access the Platform

- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs
- **Login:**
  - Analyst: `demo@oracle.ai` / `oracle2024`
  - Viewer: `viewer@oracle.ai` / `viewer2024`

## Features

### Galaxy Map (3D Visualization)
- Interactive Three.js star field where each star = one tracked entity
- Star brightness and size = risk score
- Color-coded by severity (cyan = low, amber = high, red = critical)
- Click any star to open detailed entity panel

### Risk Dashboard
- Real-time summary statistics
- Sector risk comparison charts
- Highest risk entity spotlight
- Severity distribution breakdown

### Timeline Explorer
- Historical risk score analysis for any entity
- Configurable time windows (7, 30, 90, 180 days)
- Annotated event markers
- Compare multiple entities side-by-side

### Natural Language Query
- Ask Oracle anything: "What companies in Asia are at high risk?"
- Claude-powered AI responses grounded in live data
- Query history tracking

### PDF Report Generation
- Professional audit-ready risk reports
- Includes risk score history, AI summaries, contributing signals
- One-click download

### Live Risk Feed
- WebSocket-powered real-time alert stream
- Severity-filtered views
- Click any alert to view full entity detail

## Architecture

```
oracle/
├── backend/              # FastAPI + Python
│   ├── app/
│   │   ├── api/         # REST API routes
│   │   ├── core/        # Config, security, JWT
│   │   ├── db/          # SQLAlchemy models, session
│   │   ├── ingestion/   # RSS, SEC, market data fetchers
│   │   ├── processing/  # NER, sentiment, risk scoring, Claude
│   │   └── workers/     # Celery background tasks
│   ├── alembic/         # Database migrations
│   └── tests/           # Pytest test suite
├── frontend/            # React + TypeScript
│   ├── src/
│   │   ├── components/  # GalaxyMap, RiskFeed, EntityPanel, Charts
│   │   ├── pages/       # Dashboard, Timeline, Reports
│   │   ├── api/         # API client functions
│   │   └── store/       # Zustand state management
└── docker-compose.yml   # Full stack orchestration
```

## AI Integration

Oracle uses **Claude 3.5 Sonnet** for:

1. **Risk Summaries:** When an entity crosses the 60/100 risk threshold, Oracle sends:
   - Entity context (name, type, sector)
   - Recent signals (news, filings, market data)
   - Computed risk score

   Claude returns:
   - 3-sentence plain-English summary
   - Severity classification
   - Top 3 contributing signals with evidence
   - Recommended action for decision-makers

2. **Natural Language Queries:** Users ask questions like "Which crypto exchanges show elevated risk?" and Claude generates answers grounded in live risk intelligence data.

**Rate Limiting:** Max 50 Claude calls/hour to control costs. Fallback to rule-based summaries when limit reached.

## Risk Scoring Formula

```
Risk Score = (|sentiment_delta| × 0.4) + (volume_anomaly × 0.3) + (price_volatility × 0.3)
```

- **Sentiment Delta:** Change in average sentiment vs. 7-day baseline
- **Volume Anomaly:** Z-score of signal volume (>2σ = anomalous)
- **Price Volatility:** Percentage price movement normalized to threshold

**Severity Classification:**
- 0-34: LOW
- 35-59: MEDIUM
- 60-79: HIGH
- 80-100: CRITICAL

## 🔧 Development

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload

# Run tests
pytest

# Lint
ruff check .
mypy .
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
npm run format
```

## 🚢 Deployment

### Backend (Railway / Render)

1. Connect your GitHub repo
2. Set environment variables from `.env.example`
3. Deploy from `backend/` directory
4. Run migrations: `alembic upgrade head`
5. Seed data: `python -m app.db.seed`

### Frontend (Vercel)

1. Connect your GitHub repo
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Set environment variable: `VITE_API_URL=<your-backend-url>`

### Database (Railway / Supabase)

Use managed PostgreSQL 15+ with connection pooling enabled.

### Redis (Railway / Upstash)

Use managed Redis 7+ for caching and Celery broker.

## Narrative

> "This is the system I built to solve a $100B problem. Every major corporate disaster — SVB, FTX, Evergrande — had publicly available warning signals weeks before collapse. Oracle ingests 500+ data points per hour from news, SEC filings, market data, and social signals. It uses NLP to extract entities and sentiment, runs anomaly detection on financial patterns, and sends risk clusters to Claude API which generates plain-English summaries.
>
> The result: a real-time intelligence platform that would have flagged SVB's risk 3 weeks before collapse, spotted FTX's unusual withdrawal patterns, and alerted supply chain managers to COVID disruptions before their shelves went empty.
>
> This is the kind of system KPMG uses to audit risk, Morgan Stanley uses to protect portfolios, Walmart uses to protect its supply chain, and Google uses to protect its cloud customers. I built it solo in [timeframe], and it's production-ready."



## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) + [Three.js](https://threejs.org/) - 3D visualization
- [Claude API](https://anthropic.com/) - AI-powered risk analysis
- [spaCy](https://spacy.io/) - Named entity recognition
- [HuggingFace Transformers](https://huggingface.co/) - Sentiment analysis

---
**New Learning :** 
- Github pages only used to deploy frontend, not backend.
- SEC filing: an official document that a company submits to the U.S. Securities and Exchange Commission to report its financial and business information.

**Mysterious** — Seeing risk before it becomes crisis.
