"""Search and natural language query routes."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.api.deps import CurrentUser, DBSession
from app.db.models import AISummary, Entity, RiskScore, Signal
from app.processing.claude import answer_natural_language_query
from sqlalchemy import desc

router = APIRouter(tags=["search"])


class SearchResult(BaseModel):
    """A single search result."""

    id: int
    name: str
    type: str
    sector: Optional[str]
    current_risk_score: Optional[float]
    severity: Optional[str]
    match_context: Optional[str]


class QueryRequest(BaseModel):
    """Natural language query payload."""

    question: str


class QueryResponse(BaseModel):
    """Natural language query response."""

    question: str
    answer: str
    context_entities: List[str]


@router.get("/search", response_model=List[SearchResult])
async def search_entities(
    db: DBSession,
    _: CurrentUser,
    q: str = Query(..., min_length=2),
) -> List[SearchResult]:
    """Search entities and signals by keyword."""
    search_term = f"%{q}%"

    # Search entities by name, description, sector
    entity_result = await db.execute(
        select(Entity).where(
            or_(
                Entity.name.ilike(search_term),
                Entity.description.ilike(search_term),
                Entity.sector.ilike(search_term),
                Entity.ticker.ilike(search_term),
            )
        ).limit(20)
    )
    entities = entity_result.scalars().all()

    results = []
    for entity in entities:
        # Get latest risk score
        score_result = await db.execute(
            select(RiskScore)
            .where(RiskScore.entity_id == entity.id)
            .order_by(desc(RiskScore.computed_at))
            .limit(1)
        )
        latest = score_result.scalar_one_or_none()

        results.append(
            SearchResult(
                id=entity.id,
                name=entity.name,
                type=entity.type.value,
                sector=entity.sector,
                current_risk_score=latest.score if latest else None,
                severity=latest.severity.value if latest else None,
                match_context=entity.description[:150] if entity.description else None,
            )
        )

    return results


@router.post("/query", response_model=QueryResponse)
async def natural_language_query(
    payload: QueryRequest,
    db: DBSession,
    _: CurrentUser,
) -> QueryResponse:
    """
    Accept a natural language question and return an AI-generated answer
    grounded in live risk intelligence data.
    """
    # Build context from top high-risk entities
    score_result = await db.execute(
        select(RiskScore, Entity)
        .join(Entity, RiskScore.entity_id == Entity.id)
        .order_by(desc(RiskScore.score))
        .limit(15)
    )
    top_risks = score_result.all()

    context_lines = ["Current High-Risk Entities:"]
    context_entities = []

    for risk_score, entity in top_risks:
        context_lines.append(
            f"- {entity.name} ({entity.type.value}, {entity.sector or 'General'}): "
            f"Risk Score {risk_score.score:.1f}/100 [{risk_score.severity.value}]"
        )
        context_entities.append(entity.name)

        # Add latest AI summary if available
        summary_result = await db.execute(
            select(AISummary)
            .where(AISummary.entity_id == entity.id)
            .order_by(desc(AISummary.generated_at))
            .limit(1)
        )
        summary = summary_result.scalar_one_or_none()
        if summary:
            context_lines.append(f"  Summary: {summary.summary_text[:200]}")

    context = "\n".join(context_lines)
    answer = await answer_natural_language_query(payload.question, context)

    return QueryResponse(
        question=payload.question,
        answer=answer,
        context_entities=context_entities[:5],
    )
