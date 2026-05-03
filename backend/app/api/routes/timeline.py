"""Timeline and risk history routes."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import asc, desc, select

from app.api.deps import CurrentUser, DBSession
from app.db.models import Entity, RiskScore, Signal

router = APIRouter(prefix="/timeline", tags=["timeline"])


class TimelinePoint(BaseModel):
    """A single point on the risk timeline."""

    timestamp: str
    score: float
    severity: str
    sentiment_delta: Optional[float]
    volume_anomaly: Optional[float]
    price_volatility: Optional[float]


class TimelineResponse(BaseModel):
    """Full timeline response for an entity."""

    entity_id: int
    entity_name: str
    sector: Optional[str]
    points: List[TimelinePoint]


@router.get("/{entity_id}", response_model=TimelineResponse)
async def get_entity_timeline(
    entity_id: int,
    db: DBSession,
    _: CurrentUser,
    days: int = Query(30, ge=1, le=365),
) -> TimelineResponse:
    """Return risk score history for an entity over the specified number of days."""
    entity_result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = entity_result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    scores_result = await db.execute(
        select(RiskScore)
        .where(RiskScore.entity_id == entity_id)
        .where(RiskScore.computed_at >= cutoff)
        .order_by(asc(RiskScore.computed_at))
    )
    scores = scores_result.scalars().all()

    return TimelineResponse(
        entity_id=entity.id,
        entity_name=entity.name,
        sector=entity.sector,
        points=[
            TimelinePoint(
                timestamp=rs.computed_at.isoformat(),
                score=rs.score,
                severity=rs.severity.value,
                sentiment_delta=rs.sentiment_delta,
                volume_anomaly=rs.volume_anomaly,
                price_volatility=rs.price_volatility,
            )
            for rs in scores
        ],
    )
