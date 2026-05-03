"""Watchlist management routes (analyst role required)."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import AnalystUser, DBSession
from app.db.models import Entity, RiskScore, Watchlist
from sqlalchemy import desc

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistItem(BaseModel):
    """Watchlist entry response."""

    id: int
    entity_id: int
    entity_name: str
    sector: str | None
    current_risk_score: float | None
    severity: str | None
    added_at: str


class AddToWatchlistRequest(BaseModel):
    """Request to add an entity to the watchlist."""

    entity_id: int


@router.get("", response_model=List[WatchlistItem])
async def get_watchlist(db: DBSession, current_user: AnalystUser) -> List[WatchlistItem]:
    """Return the current user's watchlist."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == current_user.user_id)
    )
    items = result.scalars().all()

    output = []
    for item in items:
        entity_result = await db.execute(select(Entity).where(Entity.id == item.entity_id))
        entity = entity_result.scalar_one_or_none()
        if not entity:
            continue

        score_result = await db.execute(
            select(RiskScore)
            .where(RiskScore.entity_id == item.entity_id)
            .order_by(desc(RiskScore.computed_at))
            .limit(1)
        )
        latest = score_result.scalar_one_or_none()

        output.append(
            WatchlistItem(
                id=item.id,
                entity_id=item.entity_id,
                entity_name=entity.name,
                sector=entity.sector,
                current_risk_score=latest.score if latest else None,
                severity=latest.severity.value if latest else None,
                added_at=item.added_at.isoformat(),
            )
        )

    return output


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    payload: AddToWatchlistRequest,
    db: DBSession,
    current_user: AnalystUser,
) -> Dict[str, Any]:
    """Add an entity to the current user's watchlist."""
    # Verify entity exists
    entity_result = await db.execute(select(Entity).where(Entity.id == payload.entity_id))
    if not entity_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    # Check for duplicate
    existing = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == current_user.user_id,
            Watchlist.entity_id == payload.entity_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Entity already in watchlist",
        )

    watchlist_item = Watchlist(user_id=current_user.user_id, entity_id=payload.entity_id)
    db.add(watchlist_item)
    await db.flush()

    return {"id": watchlist_item.id, "entity_id": payload.entity_id}


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    entity_id: int,
    db: DBSession,
    current_user: AnalystUser,
) -> None:
    """Remove an entity from the current user's watchlist."""
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == current_user.user_id,
            Watchlist.entity_id == entity_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not in watchlist")

    await db.delete(item)
