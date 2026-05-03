"""Entity management API routes."""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import desc, func, select

from app.api.deps import CurrentUser, DBSession
from app.core.config import settings
from app.db.models import AISummary, Alert, Entity, RiskScore, SeverityLevel, Signal
from app.db.session import get_redis

router = APIRouter(prefix="/entities", tags=["entities"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class EntitySummary(BaseModel):
    """Lightweight entity summary for list views."""

    id: int
    name: str
    type: str
    sector: Optional[str]
    country: Optional[str]
    ticker: Optional[str]
    current_risk_score: Optional[float]
    severity: Optional[str]
    description: Optional[str]

    model_config = {"from_attributes": True}


class RiskScoreSchema(BaseModel):
    """Risk score record."""

    id: int
    score: float
    severity: str
    computed_at: str
    sentiment_delta: Optional[float]
    volume_anomaly: Optional[float]
    price_volatility: Optional[float]


class AISummarySchema(BaseModel):
    """AI-generated risk summary."""

    id: int
    summary_text: str
    severity: str
    contributing_signals: Optional[Any]
    recommended_action: Optional[str]
    generated_at: str


class EntityDetail(BaseModel):
    """Full entity detail with risk history and AI summary."""

    id: int
    name: str
    type: str
    sector: Optional[str]
    country: Optional[str]
    ticker: Optional[str]
    description: Optional[str]
    current_risk_score: Optional[float]
    severity: Optional[str]
    latest_summary: Optional[AISummarySchema]
    recent_risk_scores: List[RiskScoreSchema]
    signal_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_latest_risk(db: DBSession, entity_id: int) -> Optional[RiskScore]:
    """Return the most recent risk score for an entity."""
    result = await db.execute(
        select(RiskScore)
        .where(RiskScore.entity_id == entity_id)
        .order_by(desc(RiskScore.computed_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("", response_model=Dict[str, Any])
async def list_entities(
    db: DBSession,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sector: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Return a paginated list of all tracked entities with current risk scores."""
    redis = await get_redis()
    cache_key = f"entities:list:{page}:{page_size}:{sector}:{severity}"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    query = select(Entity)
    if sector:
        query = query.where(Entity.sector == sector)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    entities = result.scalars().all()

    items = []
    for entity in entities:
        latest = await _get_latest_risk(db, entity.id)
        if severity and (not latest or latest.severity.value != severity):
            continue
        items.append(
            EntitySummary(
                id=entity.id,
                name=entity.name,
                type=entity.type.value,
                sector=entity.sector,
                country=entity.country,
                ticker=entity.ticker,
                current_risk_score=latest.score if latest else None,
                severity=latest.severity.value if latest else None,
                description=entity.description,
            ).model_dump()
        )

    response = {"total": total, "page": page, "page_size": page_size, "items": items}
    await redis.setex(cache_key, settings.cache_ttl_risk_scores, json.dumps(response))
    return response


@router.get("/{entity_id}", response_model=EntityDetail)
async def get_entity(entity_id: int, db: DBSession, _: CurrentUser) -> EntityDetail:
    """Return full entity detail including risk history and latest AI summary."""
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    # Latest risk score
    latest = await _get_latest_risk(db, entity_id)

    # Recent risk scores (last 30)
    scores_result = await db.execute(
        select(RiskScore)
        .where(RiskScore.entity_id == entity_id)
        .order_by(desc(RiskScore.computed_at))
        .limit(30)
    )
    recent_scores = scores_result.scalars().all()

    # Latest AI summary
    summary_result = await db.execute(
        select(AISummary)
        .where(AISummary.entity_id == entity_id)
        .order_by(desc(AISummary.generated_at))
        .limit(1)
    )
    latest_summary = summary_result.scalar_one_or_none()

    # Signal count
    count_result = await db.execute(
        select(func.count()).where(Signal.entity_id == entity_id)
    )
    signal_count = count_result.scalar_one()

    return EntityDetail(
        id=entity.id,
        name=entity.name,
        type=entity.type.value,
        sector=entity.sector,
        country=entity.country,
        ticker=entity.ticker,
        description=entity.description,
        current_risk_score=latest.score if latest else None,
        severity=latest.severity.value if latest else None,
        latest_summary=AISummarySchema(
            id=latest_summary.id,
            summary_text=latest_summary.summary_text,
            severity=latest_summary.severity.value,
            contributing_signals=latest_summary.contributing_signals,
            recommended_action=latest_summary.recommended_action,
            generated_at=latest_summary.generated_at.isoformat(),
        ) if latest_summary else None,
        recent_risk_scores=[
            RiskScoreSchema(
                id=rs.id,
                score=rs.score,
                severity=rs.severity.value,
                computed_at=rs.computed_at.isoformat(),
                sentiment_delta=rs.sentiment_delta,
                volume_anomaly=rs.volume_anomaly,
                price_volatility=rs.price_volatility,
            )
            for rs in recent_scores
        ],
        signal_count=signal_count,
    )
