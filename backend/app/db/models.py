"""SQLAlchemy ORM models for Oracle platform."""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all models."""

    pass


class EntityType(str, enum.Enum):
    """Type of tracked entity."""

    COMPANY = "company"
    COUNTRY = "country"
    SECTOR = "sector"
    PERSON = "person"


class SeverityLevel(str, enum.Enum):
    """Risk severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class UserRole(str, enum.Enum):
    """User access roles."""

    VIEWER = "viewer"
    ANALYST = "analyst"


class SignalType(str, enum.Enum):
    """Type of ingested signal."""

    NEWS = "news"
    SEC_FILING = "sec_filing"
    MARKET_DATA = "market_data"
    SOCIAL = "social"
    WIKIPEDIA = "wikipedia"


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


class User(Base):
    """Platform user with role-based access."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.VIEWER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    watchlists: Mapped[List["Watchlist"]] = relationship(back_populates="user")


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


class Entity(Base):
    """A tracked entity — company, country, sector, or person."""

    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[EntityType] = mapped_column(Enum(EntityType), nullable=False, index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    signals: Mapped[List["Signal"]] = relationship(back_populates="entity")
    risk_scores: Mapped[List["RiskScore"]] = relationship(back_populates="entity")
    ai_summaries: Mapped[List["AISummary"]] = relationship(back_populates="entity")
    alerts: Mapped[List["Alert"]] = relationship(back_populates="entity")
    watchlists: Mapped[List["Watchlist"]] = relationship(back_populates="entity")


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


class Signal(Base):
    """An ingested data signal linked to an entity."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    signal_type: Mapped[SignalType] = mapped_column(Enum(SignalType), nullable=False, index=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    entities_mentioned: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    entity: Mapped["Entity"] = relationship(back_populates="signals")

    __table_args__ = (
        Index("ix_signals_entity_published", "entity_id", "published_at"),
    )


# ---------------------------------------------------------------------------
# Risk Scores
# ---------------------------------------------------------------------------


class RiskScore(Base):
    """Computed risk score for an entity at a point in time."""

    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[SeverityLevel] = mapped_column(
        Enum(SeverityLevel), nullable=False, index=True
    )
    sentiment_delta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume_anomaly: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_volatility: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    entity: Mapped["Entity"] = relationship(back_populates="risk_scores")
    ai_summaries: Mapped[List["AISummary"]] = relationship(back_populates="risk_score")

    __table_args__ = (
        Index("ix_risk_scores_entity_computed", "entity_id", "computed_at"),
        Index("ix_risk_scores_severity_computed", "severity", "computed_at"),
    )


# ---------------------------------------------------------------------------
# AI Summaries
# ---------------------------------------------------------------------------


class AISummary(Base):
    """Claude-generated risk summary for a high-risk entity."""

    __tablename__ = "ai_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_score_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("risk_scores.id", ondelete="SET NULL"), nullable=True
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel), nullable=False)
    contributing_signals: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    entity: Mapped["Entity"] = relationship(back_populates="ai_summaries")
    risk_score: Mapped[Optional["RiskScore"]] = relationship(back_populates="ai_summaries")


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


class Alert(Base):
    """A triggered risk alert for an entity."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    severity: Mapped[SeverityLevel] = mapped_column(
        Enum(SeverityLevel), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    entity: Mapped["Entity"] = relationship(back_populates="alerts")

    __table_args__ = (
        Index("ix_alerts_severity_triggered", "severity", "triggered_at"),
    )


# ---------------------------------------------------------------------------
# Watchlists
# ---------------------------------------------------------------------------


class Watchlist(Base):
    """User watchlist entry linking a user to an entity."""

    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="watchlists")
    entity: Mapped["Entity"] = relationship(back_populates="watchlists")

    __table_args__ = (
        Index("ix_watchlists_user_entity", "user_id", "entity_id", unique=True),
    )
