"""Tests for risk scoring engine."""

import pytest
from app.processing.risk import (
    compute_risk_score,
    classify_severity,
    compute_sentiment_delta,
    compute_volume_anomaly,
    compute_price_volatility,
)
from app.db.models import SeverityLevel


def test_compute_risk_score():
    """Test risk score computation."""
    score = compute_risk_score(
        sentiment_delta=-0.8,
        volume_anomaly=0.6,
        price_volatility=0.4,
    )
    assert 0 <= score <= 100
    assert score > 50  # Should be elevated with these inputs


def test_classify_severity():
    """Test severity classification."""
    assert classify_severity(10) == SeverityLevel.LOW
    assert classify_severity(40) == SeverityLevel.MEDIUM
    assert classify_severity(65) == SeverityLevel.HIGH
    assert classify_severity(85) == SeverityLevel.CRITICAL


def test_compute_sentiment_delta():
    """Test sentiment delta calculation."""
    delta = compute_sentiment_delta(recent_avg=-0.5, baseline_avg=0.2)
    assert delta == -0.7


def test_compute_volume_anomaly():
    """Test volume anomaly detection."""
    anomaly = compute_volume_anomaly(current_volume=100, mean_volume=50, std_volume=10)
    assert anomaly > 0  # Should detect anomaly


def test_compute_price_volatility():
    """Test price volatility calculation."""
    volatility = compute_price_volatility(price_change_pct=8.0, threshold_pct=5.0)
    assert 0 <= volatility <= 1
    assert volatility > 0.5  # 8% change should be significant
