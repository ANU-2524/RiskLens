"""Risk score computation engine."""

from typing import Optional

from app.db.models import SeverityLevel


def compute_risk_score(
    sentiment_delta: float,
    volume_anomaly: float,
    price_volatility: float,
) -> float:
    """
    Compute a risk score 0–100 using the Oracle formula.

    Formula: (|sentiment_delta| × 0.4) + (volume_anomaly × 0.3) + (price_volatility × 0.3)
    All inputs are normalised to [0, 1] before weighting.
    """
    # Normalise sentiment delta: convert [-1, 1] delta to [0, 1] magnitude
    norm_sentiment = min(abs(sentiment_delta), 1.0)

    # Clamp anomaly and volatility to [0, 1]
    norm_volume = min(max(volume_anomaly, 0.0), 1.0)
    norm_price = min(max(price_volatility, 0.0), 1.0)

    raw = (norm_sentiment * 0.4) + (norm_volume * 0.3) + (norm_price * 0.3)
    return round(raw * 100, 2)


def classify_severity(score: float) -> SeverityLevel:
    """Map a numeric risk score to a severity label."""
    if score >= 80:
        return SeverityLevel.CRITICAL
    if score >= 60:
        return SeverityLevel.HIGH
    if score >= 35:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


def compute_sentiment_delta(
    recent_avg: float,
    baseline_avg: float,
) -> float:
    """
    Compute the change in sentiment relative to baseline.

    Returns a value in [-2, 2] representing the shift.
    """
    return recent_avg - baseline_avg


def compute_volume_anomaly(
    current_volume: int,
    mean_volume: float,
    std_volume: float,
) -> float:
    """
    Compute a normalised volume anomaly score.

    Returns 0 if std is zero, otherwise the z-score clamped to [0, 1].
    """
    if std_volume == 0:
        return 0.0
    z_score = (current_volume - mean_volume) / std_volume
    # Normalise: z > 2 is anomalous, cap at 1.0
    return min(max(z_score / 4.0, 0.0), 1.0)


def compute_price_volatility(
    price_change_pct: float,
    threshold_pct: float = 5.0,
) -> float:
    """
    Compute a normalised price volatility score.

    Returns 0–1 based on how far the price moved relative to a threshold.
    """
    return min(abs(price_change_pct) / (threshold_pct * 2), 1.0)
