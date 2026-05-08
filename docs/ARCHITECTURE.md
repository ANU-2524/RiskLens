# RiskLens — System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER BROWSER                                   │
│                     http://localhost:5173                                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ HTTP/WebSocket
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        REACT FRONTEND                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  Galaxy Map  │  │  Dashboard   │  │   Timeline   │                 │
│  │  (Three.js)  │  │  (Charts)    │  │   Explorer   │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  Risk Feed   │  │  Query Bar   │  │   Reports    │                 │
│  │ (WebSocket)  │  │  (Claude AI) │  │   (PDF)      │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                          │
│  State: Zustand  │  API: React Query  │  Routing: React Router         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ REST API / WebSocket
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND                                   │
│                     http://localhost:8000                                │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      API ROUTES                                   │  │
│  │  /auth  /entities  /risks  /search  /timeline  /dashboard        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 │                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │     Auth     │  │   Caching    │  │  WebSocket   │                 │
│  │     (JWT)    │  │   (Redis)    │  │   Manager    │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│      POSTGRESQL 15           │  │        REDIS 7               │
│                              │  │                              │
│  ┌────────────────────────┐ │  │  ┌────────────────────────┐ │
│  │  entities              │ │  │  │  Cache (5min TTL)      │ │
│  │  signals               │ │  │  │  Pub/Sub (WebSocket)   │ │
│  │  risk_scores           │ │  │  │  Celery Broker         │ │
│  │  ai_summaries          │ │  │  └────────────────────────┘ │
│  │  alerts                │ │  └──────────────────────────────┘
│  │  users                 │ │
│  │  watchlists            │ │
│  └────────────────────────┘ │
└──────────────────────────────┘
                    │
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CELERY WORKERS                                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    SCHEDULED TASKS                                │  │
│  │  • ingest_news_task         (every 15 min)                        │  │
│  │  • ingest_sec_task          (every 30 min)                        │  │
│  │  • ingest_market_task       (every 5 min)                         │  │
│  │  • compute_risk_scores_task (every 15 min)                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 │                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  Ingestion   │  │  Processing  │  │   AI/Claude  │                 │
│  │  (RSS, SEC)  │  │  (NER, Risk) │  │  (Summaries) │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│    EXTERNAL DATA SOURCES     │  │      CLAUDE API              │
│                              │  │                              │
│  • Reuters RSS               │  │  • Risk Summaries            │
│  • Bloomberg RSS             │  │  • NL Query Answers          │
│  • SEC EDGAR API             │  │  • Severity Classification   │
│  • Alpha Vantage API         │  │  • Action Recommendations    │
│  • Social Signals            │  │                              │
└──────────────────────────────┘  └──────────────────────────────┘
```

## 🔄 Data Flow

### 1. Data Ingestion Flow

```
External Sources → Celery Worker → Processing Pipeline → Database
                                         │
                                         ├─ NER (spaCy)
                                         ├─ Sentiment (HuggingFace)
                                         └─ Entity Matching
```

### 2. Risk Scoring Flow

```
Signals (DB) → Risk Computation → Risk Score (DB) → Alert Generation
                     │                                      │
                     ├─ Sentiment Delta                    ├─ WebSocket Broadcast
                     ├─ Volume Anomaly                     └─ Redis Pub/Sub
                     └─ Price Volatility
                            │
                            ▼
                    Claude API (if score > 60)
                            │
                            ▼
                    AI Summary (DB)
```

### 3. User Query Flow

```
User → Frontend → API → Redis Cache?
                   │         │
                   │         ├─ Hit → Return
                   │         └─ Miss ↓
                   │
                   └─ Database Query → Cache Result → Return
```

### 4. WebSocket Live Feed Flow

```
Alert Created → Redis Pub/Sub → WebSocket Manager → All Connected Clients
```

## 📦 Component Breakdown

### Backend Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Server | FastAPI | REST endpoints, WebSocket |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Migrations | Alembic | Schema versioning |
| Auth | JWT + bcrypt | Authentication |
| Cache | Redis | Response caching |
| Queue | Celery + Redis | Background jobs |
| NER | spaCy | Entity extraction |
| Sentiment | HuggingFace | Sentiment analysis |
| AI | Claude API | Risk summaries |

### Frontend Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | React 18 | Component architecture |
| Language | TypeScript | Type safety |
| 3D Graphics | Three.js | Galaxy visualization |
| Charts | Chart.js | Risk timelines |
| State | Zustand | Global state |
| API Client | React Query | Data fetching + caching |
| Routing | React Router | Navigation |
| Styling | Tailwind CSS | Cosmic theme |
| Animation | Framer Motion | Smooth transitions |
| PDF | jsPDF | Report generation |

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│  1. Network Layer                                            │
│     • CORS restrictions                                      │
│     • Rate limiting (100 req/min)                            │
│     • HTTPS in production                                    │
├─────────────────────────────────────────────────────────────┤
│  2. Authentication Layer                                     │
│     • JWT tokens (HS256)                                     │
│     • Password hashing (bcrypt)                              │
│     • Token expiration (60 min)                              │
├─────────────────────────────────────────────────────────────┤
│  3. Authorization Layer                                      │
│     • Role-based access (analyst/viewer)                     │
│     • Endpoint-level permissions                             │
│     • Resource ownership checks                              │
├─────────────────────────────────────────────────────────────┤
│  4. Data Layer                                               │
│     • SQL injection protection (ORM)                         │
│     • XSS protection (React escaping)                        │
│     • Environment variable secrets                           │
│     • No hardcoded credentials                               │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Database Schema

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    users     │       │   entities   │       │   signals    │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │◄──────┤ entity_id    │
│ email        │       │ name         │       │ source       │
│ password     │       │ type         │       │ signal_type  │
│ role         │       │ sector       │       │ raw_text     │
│ created_at   │       │ ticker       │       │ sentiment    │
└──────┬───────┘       │ created_at   │       │ published_at │
       │               └──────┬───────┘       └──────────────┘
       │                      │
       │                      │
       │               ┌──────▼───────┐       ┌──────────────┐
       │               │ risk_scores  │       │ ai_summaries │
       │               ├──────────────┤       ├──────────────┤
       │               │ id (PK)      │◄──────┤ risk_score_id│
       │               │ entity_id    │       │ entity_id    │
       │               │ score        │       │ summary_text │
       │               │ severity     │       │ severity     │
       │               │ computed_at  │       │ signals (JSON)│
       │               └──────┬───────┘       │ action       │
       │                      │               └──────────────┘
       │                      │
       │               ┌──────▼───────┐
       │               │    alerts    │
       │               ├──────────────┤
       │               │ id (PK)      │
       │               │ entity_id    │
       │               │ severity     │
       │               │ message      │
       │               │ triggered_at │
       │               └──────────────┘
       │
       │               ┌──────────────┐
       └───────────────► watchlists   │
                       ├──────────────┤
                       │ id (PK)      │
                       │ user_id      │
                       │ entity_id    │
                       │ added_at     │
                       └──────────────┘
```

## 🚀 Deployment Architecture

### Development (Docker Compose)

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host                               │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  frontend    │  │   backend    │  │celery-worker │     │
│  │  :5173       │  │   :8000      │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  postgres    │  │    redis     │  │ celery-beat  │     │
│  │  :5432       │  │   :6379      │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  Volumes: postgres_data, redis_data                         │
│  Network: RiskLens_default (bridge)                           │
└─────────────────────────────────────────────────────────────┘
```

### Production (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                         CDN                                  │
│                    (CloudFlare)                              │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  Frontend        │          │  Backend         │
│  (Vercel)        │          │  (Railway)       │
│                  │          │                  │
│  • React build   │          │  • FastAPI       │
│  • Static assets │          │  • Celery        │
│  • Edge caching  │          │  • WebSocket     │
└──────────────────┘          └────────┬─────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         │                           │
                         ▼                           ▼
              ┌──────────────────┐      ┌──────────────────┐
              │  PostgreSQL      │      │  Redis           │
              │  (Railway)       │      │  (Railway)       │
              │                  │      │                  │
              │  • Managed DB    │      │  • Managed Cache │
              │  • Auto backups  │      │  • Persistence   │
              └──────────────────┘      └──────────────────┘
```

## 🔄 CI/CD Pipeline (Recommended)

```
GitHub Push → GitHub Actions
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
   Backend Tests          Frontend Tests
   (pytest)               (npm test)
        │                       │
        ├─ Lint (ruff)          ├─ Lint (eslint)
        ├─ Type check (mypy)    ├─ Type check (tsc)
        └─ Coverage             └─ Build check
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
                    All Tests Pass?
                            │
                    ┌───────┴───────┐
                    │               │
                    ▼               ▼
              Deploy Backend   Deploy Frontend
              (Railway)        (Vercel)
                    │               │
                    └───────┬───────┘
                            │
                            ▼
                    Run Migrations
                    (alembic upgrade head)
```

## 📈 Scalability Considerations

### Horizontal Scaling

- **Backend:** Stateless API servers (scale with load balancer)
- **Celery Workers:** Add more workers for parallel processing
- **Database:** Read replicas for query distribution
- **Redis:** Redis Cluster for distributed caching

### Vertical Scaling

- **Database:** Increase CPU/RAM for complex queries
- **Redis:** Increase memory for larger cache
- **Workers:** Increase worker concurrency

### Performance Optimizations

- **Caching Strategy:** 5min TTL for risk scores, 1min for alerts
- **Database Indexes:** On entity_id, computed_at, severity
- **Connection Pooling:** SQLAlchemy pool (size=10, overflow=20)
- **Query Optimization:** Eager loading, pagination
- **CDN:** Static assets served from edge locations

---

**This architecture supports:**
- 100+ concurrent WebSocket connections
- 500+ data points ingested per hour
- Sub-200ms API response times
- 99.9% uptime with proper deployment

