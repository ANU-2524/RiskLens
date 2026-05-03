"""RSS news feed ingestion for Oracle."""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional

import feedparser
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.processing.ner import extract_entities, infer_sector
from app.processing.sentiment import score_sentiment

logger = structlog.get_logger(__name__)

RSS_FEEDS = [
    {"name": "Reuters", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},
    {"name": "AP Business", "url": "https://rsshub.app/apnews/topics/business"},
    {"name": "Financial Times", "url": "https://www.ft.com/rss/home"},
    {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss"},
]


class NewsArticle:
    """Parsed news article from an RSS feed."""

    def __init__(
        self,
        title: str,
        summary: str,
        url: str,
        source: str,
        published_at: Optional[datetime],
    ) -> None:
        """Initialise a news article."""
        self.title = title
        self.summary = summary
        self.url = url
        self.source = source
        self.published_at = published_at
        self.raw_text = f"{title}. {summary}"
        self.sentiment_score: Optional[float] = None
        self.entities: dict = {}
        self.sector: str = "General"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=False,
)
async def fetch_feed(feed_url: str, source_name: str) -> List[NewsArticle]:
    """
    Fetch and parse a single RSS feed.

    Returns a list of NewsArticle objects.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
            content = response.text
    except Exception as exc:
        logger.warning("Failed to fetch RSS feed", source=source_name, url=feed_url, error=str(exc))
        return []

    parsed = feedparser.parse(content)
    articles: List[NewsArticle] = []

    for entry in parsed.entries[:20]:  # Limit to 20 most recent per feed
        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        url = getattr(entry, "link", "")

        # Parse published date
        published_at: Optional[datetime] = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass

        if title:
            articles.append(
                NewsArticle(
                    title=title,
                    summary=summary[:1000],
                    url=url,
                    source=source_name,
                    published_at=published_at,
                )
            )

    logger.info("Fetched RSS feed", source=source_name, count=len(articles))
    return articles


async def enrich_article(article: NewsArticle) -> NewsArticle:
    """Enrich an article with NER, sentiment, and sector tagging."""
    article.sentiment_score = await score_sentiment(article.raw_text)
    article.entities = await extract_entities(article.raw_text)
    article.sector = infer_sector(article.raw_text)
    return article


async def ingest_all_feeds() -> List[NewsArticle]:
    """
    Ingest all configured RSS feeds concurrently.

    Returns all enriched articles.
    """
    logger.info("Starting news feed ingestion", feed_count=len(RSS_FEEDS))

    # Fetch all feeds concurrently
    fetch_tasks = [fetch_feed(feed["url"], feed["name"]) for feed in RSS_FEEDS]
    results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

    all_articles: List[NewsArticle] = []
    for result in results:
        if isinstance(result, list):
            all_articles.extend(result)
        elif isinstance(result, Exception):
            logger.error("Feed fetch exception", error=str(result))

    # Enrich articles concurrently (batch to avoid overwhelming NLP models)
    batch_size = 10
    enriched: List[NewsArticle] = []
    for i in range(0, len(all_articles), batch_size):
        batch = all_articles[i : i + batch_size]
        enriched_batch = await asyncio.gather(*[enrich_article(a) for a in batch])
        enriched.extend(enriched_batch)

    logger.info("News ingestion complete", total_articles=len(enriched))
    return enriched
