"""Celery background tasks for Oracle data ingestion pipeline."""

import asyncio
from typing import Any

import structlog
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

logger = structlog.get_logger(__name__)

celery_app = Celery(
    "oracle",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Schedule ingestion every 15 minutes
celery_app.conf.beat_schedule = {
    "ingest-news-feeds": {
        "task": "app.workers.tasks.ingest_news_task",
        "schedule": crontab(minute="*/15"),
    },
    "ingest-sec-filings": {
        "task": "app.workers.tasks.ingest_sec_task",
        "schedule": crontab(minute="*/30"),
    },
    "ingest-market-data": {
        "task": "app.workers.tasks.ingest_market_task",
        "schedule": crontab(minute="*/5"),
    },
    "compute-risk-scores": {
        "task": "app.workers.tasks.compute_risk_scores_task",
        "schedule": crontab(minute="*/15"),
    },
}


def run_async(coro: Any) -> Any:
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.tasks.ingest_news_task", bind=True, max_retries=3)
def ingest_news_task(self: Any) -> dict:
    """Ingest news from all RSS feeds and persist signals to the database."""
    try:
        from app.ingestion.news import ingest_all_feeds
        from app.db.session import AsyncSessionLocal
        from app.db.models import Signal, Entity, SignalType
        from sqlalchemy import select

        async def _run() -> dict:
            articles = await ingest_all_feeds()
            count = 0

            async with AsyncSessionLocal() as session:
                for article in articles:
                    # Find or skip entity matching
                    for company in article.entities.get("companies", [])[:3]:
                        result = await session.execute(
                            select(Entity).where(Entity.name.ilike(f"%{company}%")).limit(1)
                        )
                        entity = result.scalar_one_or_none()
                        if entity:
                            signal = Signal(
                                entity_id=entity.id,
                                source=article.source,
                                signal_type=SignalType.NEWS,
                                raw_text=article.raw_text[:2000],
                                url=article.url,
                                sentiment_score=article.sentiment_score,
                                published_at=article.published_at,
                                entities_mentioned=article.entities,
                            )
                            session.add(signal)
                            count += 1

                await session.commit()

            return {"articles_processed": len(articles), "signals_created": count}

        result = run_async(_run())
        logger.info("News ingestion task complete", **result)
        return result

    except Exception as exc:
        logger.error("News ingestion task failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.workers.tasks.ingest_sec_task", bind=True, max_retries=3)
def ingest_sec_task(self: Any) -> dict:
    """Ingest SEC EDGAR filings and persist signals."""
    try:
        from app.ingestion.sec import fetch_recent_filings
        from app.db.session import AsyncSessionLocal
        from app.db.models import Signal, Entity, SignalType
        from sqlalchemy import select

        async def _run() -> dict:
            filings = await fetch_recent_filings()
            count = 0

            async with AsyncSessionLocal() as session:
                for filing in filings:
                    result = await session.execute(
                        select(Entity).where(
                            Entity.name.ilike(f"%{filing.company_name[:20]}%")
                        ).limit(1)
                    )
                    entity = result.scalar_one_or_none()
                    if entity:
                        signal = Signal(
                            entity_id=entity.id,
                            source="SEC EDGAR",
                            signal_type=SignalType.SEC_FILING,
                            raw_text=filing.raw_text[:2000],
                            url=filing.url,
                            sentiment_score=filing.sentiment_score,
                            published_at=filing.filing_date,
                        )
                        session.add(signal)
                        count += 1

                await session.commit()

            return {"filings_processed": len(filings), "signals_created": count}

        result = run_async(_run())
        logger.info("SEC ingestion task complete", **result)
        return result

    except Exception as exc:
        logger.error("SEC ingestion task failed", error=str(exc))
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="app.workers.tasks.ingest_market_task", bind=True, max_retries=3)
def ingest_market_task(self: Any) -> dict:
    """Ingest market data and persist as signals."""
    try:
        from app.ingestion.market import fetch_market_data
        from app.db.session import AsyncSessionLocal
        from app.db.models import Signal, Entity, SignalType
        from sqlalchemy import select
        from datetime import datetime, timezone

        async def _run() -> dict:
            data_points = await fetch_market_data()
            count = 0

            async with AsyncSessionLocal() as session:
                for dp in data_points:
                    result = await session.execute(
                        select(Entity).where(Entity.ticker == dp.ticker).limit(1)
                    )
                    entity = result.scalar_one_or_none()
                    if entity:
                        signal = Signal(
                            entity_id=entity.id,
                            source="Market Data",
                            signal_type=SignalType.MARKET_DATA,
                            raw_text=f"{dp.ticker} price={dp.price} change={dp.change_pct}% volume={dp.volume}",
                            sentiment_score=-1.0 if dp.change_pct < -5 else (1.0 if dp.change_pct > 5 else dp.change_pct / 5),
                            published_at=datetime.now(timezone.utc),
                        )
                        session.add(signal)
                        count += 1

                await session.commit()

            return {"tickers_processed": len(data_points), "signals_created": count}

        result = run_async(_run())
        logger.info("Market data task complete", **result)
        return result

    except Exception as exc:
        logger.error("Market data task failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.workers.tasks.compute_risk_scores_task", bind=True, max_retries=3)
def compute_risk_scores_task(self: Any) -> dict:
    """Compute risk scores for all entities and trigger AI summaries for high-risk ones."""
    try:
        from app.db.session import AsyncSessionLocal
        from app.db.models import Entity, Signal, RiskScore, Alert, AISummary
        from app.processing.risk import (
            compute_risk_score,
            classify_severity,
            compute_sentiment_delta,
            compute_volume_anomaly,
        )
        from app.processing.claude import generate_risk_summary
        from sqlalchemy import select, func
        from datetime import datetime, timezone, timedelta
        import numpy as np

        async def _run() -> dict:
            scores_created = 0
            alerts_created = 0

            async with AsyncSessionLocal() as session:
                # Get all entities
                entities_result = await session.execute(select(Entity))
                entities = entities_result.scalars().all()

                now = datetime.now(timezone.utc)
                recent_window = now - timedelta(hours=24)
                baseline_window = now - timedelta(days=7)

                for entity in entities:
                    # Get recent signals
                    recent_result = await session.execute(
                        select(Signal)
                        .where(Signal.entity_id == entity.id)
                        .where(Signal.ingested_at >= recent_window)
                    )
                    recent_signals = recent_result.scalars().all()

                    if not recent_signals:
                        continue

                    # Compute sentiment delta
                    recent_sentiments = [
                        s.sentiment_score for s in recent_signals if s.sentiment_score is not None
                    ]
                    if not recent_sentiments:
                        continue

                    recent_avg = sum(recent_sentiments) / len(recent_sentiments)

                    # Get baseline signals
                    baseline_result = await session.execute(
                        select(Signal)
                        .where(Signal.entity_id == entity.id)
                        .where(Signal.ingested_at >= baseline_window)
                        .where(Signal.ingested_at < recent_window)
                    )
                    baseline_signals = baseline_result.scalars().all()
                    baseline_sentiments = [
                        s.sentiment_score for s in baseline_signals if s.sentiment_score is not None
                    ]
                    baseline_avg = (
                        sum(baseline_sentiments) / len(baseline_sentiments)
                        if baseline_sentiments
                        else 0.0
                    )

                    sentiment_delta = compute_sentiment_delta(recent_avg, baseline_avg)

                    # Volume anomaly
                    all_volumes = [1] * len(baseline_signals)
                    mean_vol = float(np.mean(all_volumes)) if all_volumes else 1.0
                    std_vol = float(np.std(all_volumes)) if len(all_volumes) > 1 else 0.5
                    volume_anomaly = compute_volume_anomaly(len(recent_signals), mean_vol, std_vol)

                    # Price volatility (from market signals)
                    market_signals = [
                        s for s in recent_signals if "change=" in (s.raw_text or "")
                    ]
                    price_volatility = 0.0
                    if market_signals:
                        try:
                            changes = []
                            for ms in market_signals:
                                parts = (ms.raw_text or "").split("change=")
                                if len(parts) > 1:
                                    pct_str = parts[1].split("%")[0]
                                    changes.append(abs(float(pct_str)))
                            if changes:
                                price_volatility = min(max(changes) / 10.0, 1.0)
                        except (ValueError, IndexError):
                            pass

                    score = compute_risk_score(sentiment_delta, volume_anomaly, price_volatility)
                    severity = classify_severity(score)

                    risk_score = RiskScore(
                        entity_id=entity.id,
                        score=score,
                        severity=severity,
                        sentiment_delta=sentiment_delta,
                        volume_anomaly=volume_anomaly,
                        price_volatility=price_volatility,
                    )
                    session.add(risk_score)
                    await session.flush()
                    scores_created += 1

                    # Create alert for HIGH/CRITICAL
                    if severity in ("HIGH", "CRITICAL"):
                        alert = Alert(
                            entity_id=entity.id,
                            severity=severity,
                            message=f"{entity.name} risk score reached {score:.1f}/100 ({severity})",
                        )
                        session.add(alert)
                        alerts_created += 1

                        # Trigger AI summary for high-risk entities
                        if score >= 60:
                            signals_data = [
                                {
                                    "signal_type": s.signal_type.value if s.signal_type else "unknown",
                                    "source": s.source,
                                    "sentiment_score": s.sentiment_score,
                                    "raw_text": s.raw_text,
                                }
                                for s in recent_signals[:10]
                            ]
                            try:
                                ai_result = await generate_risk_summary(
                                    entity_name=entity.name,
                                    entity_type=entity.type.value,
                                    risk_score=score,
                                    signals=signals_data,
                                    sector=entity.sector,
                                )
                                summary = AISummary(
                                    entity_id=entity.id,
                                    risk_score_id=risk_score.id,
                                    summary_text=ai_result["summary_text"],
                                    severity=ai_result["severity"],
                                    contributing_signals=ai_result["contributing_signals"],
                                    recommended_action=ai_result["recommended_action"],
                                    prompt_used=ai_result.get("prompt_used"),
                                )
                                session.add(summary)
                            except Exception as exc:
                                logger.error("AI summary failed", entity=entity.name, error=str(exc))

                await session.commit()

            return {"scores_created": scores_created, "alerts_created": alerts_created}

        result = run_async(_run())
        logger.info("Risk score computation complete", **result)
        return result

    except Exception as exc:
        logger.error("Risk score task failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)
