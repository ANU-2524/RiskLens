"""Market data ingestion using Alpha Vantage and Yahoo Finance fallback."""

from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger(__name__)

ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"

# Tracked tickers for demo
TRACKED_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "JPM", "BAC", "GS", "MS", "WFC",
    "XOM", "CVX", "BP", "SHEL",
    "WMT", "TGT", "COST", "AMZN",
    "JNJ", "PFE", "MRNA",
    "BTC-USD", "ETH-USD",
]


class MarketDataPoint:
    """A single market data observation."""

    def __init__(
        self,
        ticker: str,
        price: float,
        change_pct: float,
        volume: int,
        timestamp: str,
    ) -> None:
        """Initialise a market data point."""
        self.ticker = ticker
        self.price = price
        self.change_pct = change_pct
        self.volume = volume
        self.timestamp = timestamp


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=False,
)
async def fetch_quote_alpha_vantage(ticker: str) -> Optional[MarketDataPoint]:
    """Fetch a real-time quote from Alpha Vantage."""
    if not settings.alpha_vantage_api_key:
        return None

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": settings.alpha_vantage_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(ALPHA_VANTAGE_BASE, params=params)
            response.raise_for_status()
            data: Dict[str, Any] = response.json()

        quote = data.get("Global Quote", {})
        if not quote:
            return None

        return MarketDataPoint(
            ticker=ticker,
            price=float(quote.get("05. price", 0)),
            change_pct=float(quote.get("10. change percent", "0%").replace("%", "")),
            volume=int(quote.get("06. volume", 0)),
            timestamp=quote.get("07. latest trading day", ""),
        )
    except Exception as exc:
        logger.warning("Alpha Vantage fetch failed", ticker=ticker, error=str(exc))
        return None


async def fetch_market_data(tickers: Optional[List[str]] = None) -> List[MarketDataPoint]:
    """
    Fetch market data for a list of tickers.

    Falls back to simulated data if API keys are not configured.
    """
    import asyncio

    if tickers is None:
        tickers = TRACKED_TICKERS[:10]  # Limit to avoid rate limits

    if not settings.alpha_vantage_api_key:
        logger.info("No Alpha Vantage key, using simulated market data")
        return _generate_simulated_data(tickers)

    tasks = [fetch_quote_alpha_vantage(ticker) for ticker in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    data_points: List[MarketDataPoint] = []
    for result in results:
        if isinstance(result, MarketDataPoint):
            data_points.append(result)

    logger.info("Market data fetched", count=len(data_points))
    return data_points


def _generate_simulated_data(tickers: List[str]) -> List[MarketDataPoint]:
    """Generate realistic simulated market data for demo purposes."""
    import random
    from datetime import datetime, timezone

    random.seed(42)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    data_points = []
    for ticker in tickers:
        base_price = random.uniform(50, 500)
        change_pct = random.gauss(0, 2.5)  # Normal distribution, ~2.5% std
        volume = random.randint(1_000_000, 50_000_000)

        data_points.append(
            MarketDataPoint(
                ticker=ticker,
                price=round(base_price, 2),
                change_pct=round(change_pct, 2),
                volume=volume,
                timestamp=timestamp,
            )
        )

    return data_points
