"""Dashboard summary statistics routes."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter
from sqlalchemy import desc, func, select

from app.api.deps import CurrentUser, DBSession
from app.core.config import settings
from app.db.models import Alert, Entity, RiskScore, SeverityLevel
from app.db.session import get_redis

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(db: DBSession, _: CurrentUser) -> Dict[str, Any]:
    """Return summary statistics for the main dashboard."""
    redis = await get_redis()
    cache_key = "dashboard:stats"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Total entities
    entity_count_result = await db.execute(select(func.count()).select_from(Entity))
    total_entities = entity_count_result.scalar_one()

    # Alerts today
    alerts_today_result = await db.execute(
        select(func.count())
        .select_from(Alert)
        .where(Alert.triggered_at >= today_start)
    )
    alerts_today = alerts_today_result.scalar_one()

    # Critical alerts today
    critical_today_result = await db.execute(
        select(func.count())
        .select_from(Alert)
        .where(Alert.triggered_at >= today_start)
        .where(Alert.severity == SeverityLevel.CRITICAL)
    )
    critical_today = critical_today_result.scalar_one()

    # Highest risk entity
    highest_result = await db.execute(
        select(RiskScore, Entity)
        .join(Entity, RiskScore.entity_id == Entity.id)
        .order_by(desc(RiskScore.score))
        .limit(1)
    )
    highest = highest_result.first()

    highest_entity: Optional[Dict[str, Any]] = None
    if highest:
        risk_score, entity = highest
        highest_entity = {
            "id": entity.id,
            "name": entity.name,
            "score": risk_score.score,
            "severity": risk_score.severity.value,
            "sector": entity.sector,
        }

    # Average risk score across all entities
    avg_result = await db.execute(
        select(func.avg(RiskScore.score)).select_from(RiskScore)
    )
    avg_score = avg_result.scalar_one() or 0.0

    # Severity distribution
    severity_result = await db.execute(
        select(RiskScore.severity, func.count())
        .group_by(RiskScore.severity)
    )
    severity_dist = {row[0].value: row[1] for row in severity_result.all()}

    stats = {
        "total_entities": total_entities,
        "alerts_today": alerts_today,
        "critical_today": critical_today,
        "avg_risk_score": round(float(avg_score), 2),
        "highest_risk_entity": highest_entity,
        "severity_distribution": severity_dist,
        "last_updated": now.isoformat(),
    }

    await redis.setex(cache_key, settings.cache_ttl_risk_scores, json.dumps(stats))
    return stats
