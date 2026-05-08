"""
Database seeding script — pre-populates RiskLens with realistic historical data
demonstrating the platform's predictive capabilities for demo purposes.

Covers: SVB collapse, Evergrande crisis, COVID supply chain, FTX collapse,
Russia-Ukraine energy impact.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AISummary,
    Alert,
    Base,
    Entity,
    EntityType,
    RiskScore,
    SeverityLevel,
    Signal,
    SignalType,
    User,
    UserRole,
)
from app.db.session import AsyncSessionLocal, engine
from app.core.security import hash_password

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Entity definitions
# ---------------------------------------------------------------------------

SEED_ENTITIES = [
    # Finance
    {"name": "Silicon Valley Bank", "type": EntityType.COMPANY, "sector": "Finance", "ticker": "SIVB", "country": "USA", "description": "Regional bank serving tech startups and venture capital firms."},
    {"name": "JPMorgan Chase", "type": EntityType.COMPANY, "sector": "Finance", "ticker": "JPM", "country": "USA", "description": "Largest US bank by assets."},
    {"name": "Goldman Sachs", "type": EntityType.COMPANY, "sector": "Finance", "ticker": "GS", "country": "USA", "description": "Global investment banking and financial services."},
    {"name": "Morgan Stanley", "type": EntityType.COMPANY, "sector": "Finance", "ticker": "MS", "country": "USA", "description": "Global financial services firm."},
    {"name": "Credit Suisse", "type": EntityType.COMPANY, "sector": "Finance", "ticker": "CS", "country": "Switzerland", "description": "Swiss multinational investment bank."},
    # Crypto
    {"name": "FTX Exchange", "type": EntityType.COMPANY, "sector": "Crypto", "ticker": "FTT", "country": "Bahamas", "description": "Cryptocurrency exchange founded by Sam Bankman-Fried."},
    {"name": "Binance", "type": EntityType.COMPANY, "sector": "Crypto", "ticker": "BNB", "country": "Global", "description": "World's largest cryptocurrency exchange by volume."},
    # Real Estate
    {"name": "Evergrande Group", "type": EntityType.COMPANY, "sector": "Real Estate", "ticker": "3333.HK", "country": "China", "description": "Chinese property developer, one of the world's most indebted companies."},
    {"name": "Country Garden", "type": EntityType.COMPANY, "sector": "Real Estate", "ticker": "2007.HK", "country": "China", "description": "China's largest property developer by sales."},
    # Energy
    {"name": "Gazprom", "type": EntityType.COMPANY, "sector": "Energy", "ticker": "GAZP", "country": "Russia", "description": "Russian state-controlled energy corporation."},
    {"name": "ExxonMobil", "type": EntityType.COMPANY, "sector": "Energy", "ticker": "XOM", "country": "USA", "description": "American multinational oil and gas corporation."},
    {"name": "BP", "type": EntityType.COMPANY, "sector": "Energy", "ticker": "BP", "country": "UK", "description": "British multinational oil and gas company."},
    # Retail / Supply Chain
    {"name": "Walmart", "type": EntityType.COMPANY, "sector": "Retail", "ticker": "WMT", "country": "USA", "description": "World's largest retailer by revenue."},
    {"name": "Amazon", "type": EntityType.COMPANY, "sector": "Retail", "ticker": "AMZN", "country": "USA", "description": "E-commerce and cloud computing giant."},
    {"name": "Target", "type": EntityType.COMPANY, "sector": "Retail", "ticker": "TGT", "country": "USA", "description": "American retail corporation."},
    # Technology
    {"name": "Apple", "type": EntityType.COMPANY, "sector": "Technology", "ticker": "AAPL", "country": "USA", "description": "Consumer electronics and software company."},
    {"name": "Microsoft", "type": EntityType.COMPANY, "sector": "Technology", "ticker": "MSFT", "country": "USA", "description": "Cloud computing and software giant."},
    {"name": "NVIDIA", "type": EntityType.COMPANY, "sector": "Technology", "ticker": "NVDA", "country": "USA", "description": "Semiconductor company specialising in GPUs and AI chips."},
    # Healthcare
    {"name": "Pfizer", "type": EntityType.COMPANY, "sector": "Healthcare", "ticker": "PFE", "country": "USA", "description": "Multinational pharmaceutical corporation."},
    {"name": "Johnson & Johnson", "type": EntityType.COMPANY, "sector": "Healthcare", "ticker": "JNJ", "country": "USA", "description": "Multinational healthcare corporation."},
    # Countries / Geopolitical
    {"name": "Russia", "type": EntityType.COUNTRY, "sector": "Energy", "country": "Russia", "description": "Major energy exporter facing international sanctions."},
    {"name": "China", "type": EntityType.COUNTRY, "sector": "Real Estate", "country": "China", "description": "World's second-largest economy with property sector stress."},
    {"name": "Ukraine", "type": EntityType.COUNTRY, "sector": "General", "country": "Ukraine", "description": "Eastern European nation in active conflict with Russia."},
    # Sectors
    {"name": "Global Supply Chain", "type": EntityType.SECTOR, "sector": "Retail", "description": "Aggregate risk indicator for global logistics and supply chains."},
    {"name": "Cryptocurrency Market", "type": EntityType.SECTOR, "sector": "Crypto", "description": "Aggregate risk indicator for the cryptocurrency ecosystem."},
]


# ---------------------------------------------------------------------------
# Historical event signal generators
# ---------------------------------------------------------------------------

def _days_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=n)


def _make_svb_signals(entity_id: int) -> List[dict]:
    """Generate SVB collapse signals — risk should escalate 3 weeks before March 10, 2023."""
    base = _days_ago(1100)  # ~March 2023 equivalent in demo time
    signals = []

    # Week 1: Early warning signs
    for i in range(7):
        signals.append({
            "entity_id": entity_id, "source": "Reuters",
            "signal_type": SignalType.NEWS,
            "raw_text": f"SVB Financial Group reports significant unrealised losses in bond portfolio. Rising interest rates creating pressure on held-to-maturity securities. Day {i+1} of monitoring.",
            "sentiment_score": -0.3 - (i * 0.05),
            "published_at": base + timedelta(days=i),
        })

    # Week 2: Escalation
    for i in range(7, 14):
        signals.append({
            "entity_id": entity_id, "source": "Financial Times",
            "signal_type": SignalType.NEWS,
            "raw_text": f"SVB customers begin withdrawing deposits amid concerns about bank stability. Venture capital firms advising portfolio companies to diversify banking relationships. Unusual withdrawal volume detected.",
            "sentiment_score": -0.6 - ((i - 7) * 0.04),
            "published_at": base + timedelta(days=i),
        })
        signals.append({
            "entity_id": entity_id, "source": "SEC EDGAR",
            "signal_type": SignalType.SEC_FILING,
            "raw_text": f"SVB Financial 8-K: Company announces sale of available-for-sale securities portfolio at $1.8B loss. Capital raise planned.",
            "sentiment_score": -0.75,
            "published_at": base + timedelta(days=i),
        })

    # Week 3: Critical
    for i in range(14, 21):
        signals.append({
            "entity_id": entity_id, "source": "Bloomberg",
            "signal_type": SignalType.NEWS,
            "raw_text": f"Bank run accelerating at SVB. $42 billion withdrawal attempt in single day. FDIC intervention imminent. Stock halted.",
            "sentiment_score": -0.95,
            "published_at": base + timedelta(days=i),
        })

    return signals


def _make_ftx_signals(entity_id: int) -> List[dict]:
    """Generate FTX collapse signals — escalating before November 2022 collapse."""
    base = _days_ago(1250)
    signals = []

    for i in range(5):
        signals.append({
            "entity_id": entity_id, "source": "CoinDesk",
            "signal_type": SignalType.NEWS,
            "raw_text": f"CoinDesk report reveals Alameda Research balance sheet heavily concentrated in FTT tokens. Circular relationship between FTX and Alameda raises solvency questions.",
            "sentiment_score": -0.4 - (i * 0.08),
            "published_at": base + timedelta(days=i),
        })

    for i in range(5, 12):
        signals.append({
            "entity_id": entity_id, "source": "Twitter/X",
            "signal_type": SignalType.SOCIAL,
            "raw_text": f"Binance CEO announces sale of all FTT holdings. Massive FTT token sell-off begins. Withdrawal requests surging on FTX platform. Liquidity crisis emerging.",
            "sentiment_score": -0.85,
            "published_at": base + timedelta(days=i),
        })

    for i in range(12, 18):
        signals.append({
            "entity_id": entity_id, "source": "Reuters",
            "signal_type": SignalType.NEWS,
            "raw_text": f"FTX halts withdrawals. Sam Bankman-Fried seeks emergency funding. Binance acquisition deal collapses. FTX files for Chapter 11 bankruptcy.",
            "sentiment_score": -0.99,
            "published_at": base + timedelta(days=i),
        })

    return signals


def _make_evergrande_signals(entity_id: int) -> List[dict]:
    """Generate Evergrande debt crisis signals — 2021."""
    base = _days_ago(1600)
    signals = []

    for i in range(10):
        signals.append({
            "entity_id": entity_id, "source": "Bloomberg",
            "signal_type": SignalType.NEWS,
            "raw_text": f"Evergrande Group faces mounting debt obligations exceeding $300 billion. Chinese property sector showing systemic stress. Suppliers and contractors unpaid.",
            "sentiment_score": -0.5 - (i * 0.04),
            "published_at": base + timedelta(days=i * 3),
        })

    for i in range(10, 20):
        signals.append({
            "entity_id": entity_id, "source": "Financial Times",
            "signal_type": SignalType.NEWS,
            "raw_text": f"Evergrande misses bond coupon payment. Contagion spreading to other Chinese property developers. Beijing signals limited bailout. Global markets rattled.",
            "sentiment_score": -0.88,
            "published_at": base + timedelta(days=i * 3),
        })

    return signals


def _make_covid_supply_chain_signals(entity_id: int) -> List[dict]:
    """Generate COVID supply chain disruption signals — 2020."""
    base = _days_ago(2200)
    signals = []

    for i in range(15):
        signals.append({
            "entity_id": entity_id, "source": "AP News",
            "signal_type": SignalType.NEWS,
            "raw_text": f"COVID-19 lockdowns in China disrupting manufacturing. Port congestion at record levels. Container shipping costs surging 400%. Retail inventory shortages emerging globally.",
            "sentiment_score": -0.6 - (i * 0.02),
            "published_at": base + timedelta(days=i * 5),
        })

    return signals


def _make_russia_energy_signals(entity_id: int) -> List[dict]:
    """Generate Russia-Ukraine energy impact signals — 2022."""
    base = _days_ago(1400)
    signals = []

    for i in range(12):
        signals.append({
            "entity_id": entity_id, "source": "Reuters",
            "signal_type": SignalType.NEWS,
            "raw_text": f"Russia invades Ukraine. European energy crisis deepens as gas supplies cut. Natural gas prices surge 300%. Germany activates emergency energy plan. Gazprom halts Nord Stream deliveries.",
            "sentiment_score": -0.7 - (i * 0.02),
            "published_at": base + timedelta(days=i * 4),
        })

    return signals


def _make_risk_scores(entity_id: int, signals: List[dict]) -> List[dict]:
    """Generate risk score progression matching the signal timeline."""
    if not signals:
        return []

    scores = []
    sorted_signals = sorted(signals, key=lambda s: s["published_at"])

    # Group signals by week and compute escalating scores
    for i, signal in enumerate(sorted_signals):
        progress = i / max(len(sorted_signals) - 1, 1)
        base_score = 20 + (progress * 75)
        sentiment = abs(signal["sentiment_score"])
        score = min(base_score * (0.5 + sentiment * 0.5), 100)

        if score >= 80:
            severity = SeverityLevel.CRITICAL
        elif score >= 60:
            severity = SeverityLevel.HIGH
        elif score >= 35:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW

        scores.append({
            "entity_id": entity_id,
            "score": round(score, 2),
            "severity": severity,
            "sentiment_delta": signal["sentiment_score"],
            "volume_anomaly": min(progress * 0.8, 1.0),
            "price_volatility": min(progress * 0.6, 1.0),
            "computed_at": signal["published_at"],
        })

    return scores


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------


async def seed_database() -> None:
    """Seed the database with entities, historical signals, and risk scores."""
    logger.info("Starting database seed")

    async with AsyncSessionLocal() as session:
        # Create demo users
        await _create_users(session)

        # Create entities
        entity_map = await _create_entities(session)
        await session.flush()

        # Generate historical signals for key events
        all_signals: List[dict] = []
        all_scores: List[dict] = []
        all_alerts: List[dict] = []
        all_summaries: List[dict] = []

        event_map = {
            "Silicon Valley Bank": (_make_svb_signals, "SVB showed critical risk signals 3 weeks before collapse. Unrealised bond losses, unusual withdrawal patterns, and VC advisor communications all pointed to imminent failure. RiskLens flagged CRITICAL status on March 1, 2023 — 9 days before FDIC seizure."),
            "FTX Exchange": (_make_ftx_signals, "FTX exhibited classic pre-collapse patterns: circular token relationships, unusual withdrawal velocity, and social sentiment collapse. RiskLens flagged HIGH risk when CoinDesk published the Alameda balance sheet — 8 days before bankruptcy filing."),
            "Evergrande Group": (_make_evergrande_signals, "Evergrande's debt spiral was visible in SEC-equivalent filings and supplier payment delays months before default. RiskLens detected systemic property sector stress and flagged CRITICAL status 6 weeks before the missed bond payment."),
            "Global Supply Chain": (_make_covid_supply_chain_signals, "COVID supply chain disruption signals emerged in port congestion data and shipping cost indices weeks before retail shelves emptied. RiskLens's cross-source correlation identified the risk pattern early."),
            "Gazprom": (_make_russia_energy_signals, "Russia-Ukraine conflict energy impact was predictable from geopolitical signals and gas flow data. RiskLens flagged European energy sector CRITICAL status within 48 hours of invasion, enabling early hedging."),
        }

        for entity_name, (signal_fn, summary_text) in event_map.items():
            entity_id = entity_map.get(entity_name)
            if not entity_id:
                continue

            signals = signal_fn(entity_id)
            scores = _make_risk_scores(entity_id, signals)

            all_signals.extend(signals)
            all_scores.extend(scores)

            if scores:
                peak = max(scores, key=lambda s: s["score"])
                all_alerts.append({
                    "entity_id": entity_id,
                    "severity": peak["severity"],
                    "message": f"RiskLens detected {peak['severity'].value} risk for {entity_name}. Score: {peak['score']:.1f}/100",
                    "triggered_at": peak["computed_at"],
                    "acknowledged": True,
                })
                all_summaries.append({
                    "entity_id": entity_id,
                    "summary_text": summary_text,
                    "severity": peak["severity"],
                    "contributing_signals": [
                        {"signal": "Sentiment collapse", "evidence": f"Sentiment score reached {min(s['sentiment_score'] for s in signals):.2f}"},
                        {"signal": "Volume anomaly", "evidence": "Signal volume 3.2x above 30-day baseline"},
                        {"signal": "Cross-source correlation", "evidence": "News, SEC filings, and social signals all aligned"},
                    ],
                    "recommended_action": "Reduce exposure immediately. Escalate to risk committee. Prepare contingency plans.",
                    "generated_at": peak["computed_at"],
                })

        # Add current-day signals for live demo feel
        all_signals.extend(_make_current_signals(entity_map))

        # Bulk insert
        for signal_data in all_signals:
            session.add(Signal(**signal_data))

        await session.flush()

        for score_data in all_scores:
            session.add(RiskScore(**score_data))

        await session.flush()

        for alert_data in all_alerts:
            session.add(Alert(**alert_data))

        for summary_data in all_summaries:
            session.add(AISummary(**summary_data))

        await session.commit()

    logger.info(
        "Database seed complete",
        entities=len(SEED_ENTITIES),
        signals=len(all_signals),
        scores=len(all_scores),
    )


async def _create_users(session: AsyncSession) -> None:
    """Create demo users."""
    from sqlalchemy import select
    existing = await session.execute(select(User).limit(1))
    if existing.scalar_one_or_none():
        return

    users = [
        User(email="demo@RiskLens.ai", hashed_password=hash_password("RiskLens2024"), role=UserRole.ANALYST),
        User(email="viewer@RiskLens.ai", hashed_password=hash_password("viewer2024"), role=UserRole.VIEWER),
    ]
    for user in users:
        session.add(user)
    logger.info("Demo users created")


async def _create_entities(session: AsyncSession) -> dict:
    """Create all seed entities and return name→id mapping."""
    from sqlalchemy import select
    entity_map = {}

    for entity_data in SEED_ENTITIES:
        existing = await session.execute(
            select(Entity).where(Entity.name == entity_data["name"])
        )
        entity = existing.scalar_one_or_none()
        if not entity:
            entity = Entity(**entity_data)
            session.add(entity)
            await session.flush()

        entity_map[entity_data["name"]] = entity.id

    logger.info("Entities created/verified", count=len(entity_map))
    return entity_map


def _make_current_signals(entity_map: dict) -> List[dict]:
    """Generate recent signals for a live demo feel."""
    now = datetime.now(timezone.utc)
    signals = []

    current_events = [
        ("Apple", "Apple supply chain faces disruption as Taiwan Strait tensions escalate. TSMC production capacity at risk.", -0.45, SignalType.NEWS, "Reuters"),
        ("NVIDIA", "NVIDIA AI chip export restrictions tightened. China revenue at risk. Stock volatility elevated.", -0.38, SignalType.NEWS, "Bloomberg"),
        ("JPMorgan Chase", "JPMorgan Q1 earnings beat expectations. Credit loss provisions increasing amid commercial real estate concerns.", -0.15, SignalType.SEC_FILING, "SEC EDGAR"),
        ("Binance", "Binance faces regulatory scrutiny in multiple jurisdictions. Withdrawal volumes elevated. Compliance costs rising.", -0.55, SignalType.NEWS, "Financial Times"),
        ("Walmart", "Walmart supply chain resilience improving post-COVID. Inventory levels normalising. Consumer spending holding.", 0.35, SignalType.NEWS, "AP News"),
        ("Pfizer", "Pfizer COVID vaccine revenue declining sharply. Pipeline concerns. Cost-cutting measures announced.", -0.42, SignalType.NEWS, "Reuters"),
        ("Gazprom", "Gazprom revenue declining as European customers diversify energy sources. LNG competition intensifying.", -0.6, SignalType.NEWS, "Bloomberg"),
        ("Credit Suisse", "Credit Suisse integration into UBS progressing. Legacy risk positions being unwound. Regulatory capital improving.", 0.2, SignalType.NEWS, "Financial Times"),
    ]

    for entity_name, text, sentiment, signal_type, source in current_events:
        entity_id = entity_map.get(entity_name)
        if entity_id:
            signals.append({
                "entity_id": entity_id,
                "source": source,
                "signal_type": signal_type,
                "raw_text": text,
                "sentiment_score": sentiment,
                "published_at": now - timedelta(hours=len(signals) * 2),
            })

    return signals


if __name__ == "__main__":
    asyncio.run(seed_database())

