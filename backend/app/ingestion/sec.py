"""SEC EDGAR filing ingestion for RiskLens."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.processing.sentiment import score_sentiment

logger = structlog.get_logger(__name__)

EDGAR_BASE_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index?q=%22{query}%22&dateRange=custom&startdt={start}&enddt={end}&forms={forms}"
EDGAR_COMPANY_SEARCH = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={name}&type={form_type}&dateb=&owner=include&count=10&search_text=&output=atom"

WATCHED_FORM_TYPES = ["8-K", "10-K", "10-Q"]


class SECFiling:
    """Parsed SEC EDGAR filing."""

    def __init__(
        self,
        company_name: str,
        form_type: str,
        filing_date: Optional[datetime],
        description: str,
        url: str,
        cik: str,
    ) -> None:
        """Initialise a SEC filing."""
        self.company_name = company_name
        self.form_type = form_type
        self.filing_date = filing_date
        self.description = description
        self.url = url
        self.cik = cik
        self.raw_text = f"{company_name} {form_type}: {description}"
        self.sentiment_score: Optional[float] = None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=False,
)
async def fetch_recent_filings(
    form_types: Optional[List[str]] = None,
    days_back: int = 1,
) -> List[SECFiling]:
    """
    Fetch recent SEC EDGAR filings using the full-text search API.

    Returns a list of SECFiling objects.
    """
    if form_types is None:
        form_types = WATCHED_FORM_TYPES

    from datetime import timedelta
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)

    forms_param = ",".join(form_types)
    url = (
        f"https://efts.sec.gov/LATEST/search-index?q=%22risk%22"
        f"&dateRange=custom"
        f"&startdt={start_date.strftime('%Y-%m-%d')}"
        f"&enddt={end_date.strftime('%Y-%m-%d')}"
        f"&forms={forms_param}"
    )

    filings: List[SECFiling] = []

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            headers={"User-Agent": "RiskLens Risk Intelligence RiskLens@example.com"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            data: Dict[str, Any] = response.json()

        hits = data.get("hits", {}).get("hits", [])
        for hit in hits[:20]:
            source = hit.get("_source", {})
            company_name = source.get("entity_name", ["Unknown"])[0] if source.get("entity_name") else "Unknown"
            form_type = source.get("form_type", "")
            description = source.get("file_date", "") + " " + source.get("period_of_report", "")
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{source.get('entity_id', '')}/{source.get('file_num', '')}"

            filing_date: Optional[datetime] = None
            if source.get("file_date"):
                try:
                    filing_date = datetime.strptime(source["file_date"], "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    pass

            filings.append(
                SECFiling(
                    company_name=company_name,
                    form_type=form_type,
                    filing_date=filing_date,
                    description=description[:500],
                    url=filing_url,
                    cik=str(source.get("entity_id", "")),
                )
            )

    except Exception as exc:
        logger.warning("SEC EDGAR fetch failed", error=str(exc))
        return []

    # Enrich with sentiment
    for filing in filings:
        try:
            filing.sentiment_score = await score_sentiment(filing.raw_text)
        except Exception:
            filing.sentiment_score = 0.0

    logger.info("SEC filings ingested", count=len(filings))
    return filings

