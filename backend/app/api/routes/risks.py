"""Risk alerts and live feed API routes."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import desc, select

from app.api.deps import CurrentUser, DBSession
from app.core.config import settings
from app.db.models import Alert, AISummary, Entity, RiskScore, SeverityLevel
from app.db.session import get_redis

router = APIRouter(prefix="/risks", tags=["risks"])


class AlertSchema(BaseModel):
    """Alert response schema."""

    id: int
    entity_id: int
    entity_name: str
    severity: str
    message: str
    triggered_at: str
    acknowledged: bool
    current_score: Optional[float]
    ai_summary: Optional[str]


@router.get("/alerts", response_model=List[AlertSchema])
async def get_recent_alerts(
    db: DBSession,
    _: CurrentUser,
    hours: int = Query(24, ge=1, le=168),
    severity: Optional[str] = Query(None),
) -> List[AlertSchema]:
    """Return recent HIGH and CRITICAL alerts from the last N hours."""
    redis = await get_redis()
    cache_key = f"alerts:recent:{hours}:{severity}"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = (
        select(Alert)
        .where(Alert.triggered_at >= cutoff)
        .where(Alert.severity.in_([SeverityLevel.HIGH, SeverityLevel.CRITICAL]))
        .order_by(desc(Alert.triggered_at))
        .limit(100)
    )

    if severity:
        query = select(Alert).where(Alert.triggered_at >= cutoff).where(
            Alert.severity == severity
        ).order_by(desc(Alert.triggered_at)).limit(100)

    result = await db.execute(query)
    alerts = result.scalars().all()

    items = []
    for alert in alerts:
        # Get entity name
        entity_result = await db.execute(select(Entity).where(Entity.id == alert.entity_id))
        entity = entity_result.scalar_one_or_none()

        # Get latest risk score
        score_result = await db.execute(
            select(RiskScore)
            .where(RiskScore.entity_id == alert.entity_id)
            .order_by(desc(RiskScore.computed_at))
            .limit(1)
        )
        latest_score = score_result.scalar_one_or_none()

        # Get latest AI summary
        summary_result = await db.execute(
            select(AISummary)
            .where(AISummary.entity_id == alert.entity_id)
            .order_by(desc(AISummary.generated_at))
            .limit(1)
        )
        latest_summary = summary_result.scalar_one_or_none()

        items.append(
            AlertSchema(
                id=alert.id,
                entity_id=alert.entity_id,
                entity_name=entity.name if entity else "Unknown",
                severity=alert.severity.value,
                message=alert.message,
                triggered_at=alert.triggered_at.isoformat(),
                acknowledged=alert.acknowledged,
                current_score=latest_score.score if latest_score else None,
                ai_summary=latest_summary.summary_text[:200] if latest_summary else None,
            ).model_dump()
        )

    await redis.setex(cache_key, settings.cache_ttl_live_alerts, json.dumps(items))
    return items


@router.get("/sectors", response_model=List[Dict[str, Any]])
async def get_sector_risks(db: DBSession, _: CurrentUser) -> List[Dict[str, Any]]:
    """Return risk aggregated by sector."""
    redis = await get_redis()
    cache_key = "risks:sectors"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    from sqlalchemy import func, Float
    from app.db.models import Entity, RiskScore

    # Get latest risk score per entity, grouped by sector
    result = await db.execute(select(Entity))
    entities = result.scalars().all()

    sector_data: Dict[str, Dict[str, Any]] = {}

    for entity in entities:
        if not entity.sector:
            continue

        score_result = await db.execute(
            select(RiskScore)
            .where(RiskScore.entity_id == entity.id)
            .order_by(desc(RiskScore.computed_at))
            .limit(1)
        )
        latest = score_result.scalar_one_or_none()
        if not latest:
            continue

        sector = entity.sector
        if sector not in sector_data:
            sector_data[sector] = {
                "sector": sector,
                "entity_count": 0,
                "avg_risk_score": 0.0,
                "max_risk_score": 0.0,
                "top_entity": None,
                "scores": [],
            }

        sector_data[sector]["entity_count"] += 1
        sector_data[sector]["scores"].append(latest.score)
        if latest.score > sector_data[sector]["max_risk_score"]:
            sector_data[sector]["max_risk_score"] = latest.score
            sector_data[sector]["top_entity"] = entity.name

    # Compute averages and clean up
    output = []
    for sector, data in sector_data.items():
        scores = data.pop("scores")
        data["avg_risk_score"] = round(sum(scores) / len(scores), 2) if scores else 0.0
        output.append(data)

    output.sort(key=lambda x: x["avg_risk_score"], reverse=True)

    await redis.setex(cache_key, settings.cache_ttl_risk_scores, json.dumps(output))
    return output
