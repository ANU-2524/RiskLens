"""Sentiment scoring using HuggingFace transformers with fallback."""

import asyncio
import re
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

_sentiment_pipeline = None


def _get_pipeline():
    """Lazy-load the sentiment pipeline."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        try:
            from transformers import pipeline
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                truncation=True,
                max_length=512,
            )
            logger.info("Loaded HuggingFace sentiment pipeline")
        except Exception as exc:
            logger.warning("Could not load HuggingFace pipeline, using lexicon fallback", error=str(exc))
            _sentiment_pipeline = "fallback"
    return _sentiment_pipeline


# Simple lexicon for fallback scoring
_POSITIVE_WORDS = {
    "growth", "profit", "gain", "surge", "rally", "strong", "beat", "record",
    "upgrade", "positive", "recovery", "expansion", "success", "innovation",
}
_NEGATIVE_WORDS = {
    "loss", "decline", "crash", "collapse", "fraud", "bankruptcy", "default",
    "risk", "warning", "investigation", "lawsuit", "scandal", "crisis", "fail",
    "downgrade", "negative", "concern", "volatile", "uncertainty", "debt",
}


def _lexicon_score(text: str) -> float:
    """Simple lexicon-based sentiment score in [-1, 1]."""
    words = set(re.findall(r"\b\w+\b", text.lower()))
    pos = len(words & _POSITIVE_WORDS)
    neg = len(words & _NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def _score_sync(text: str) -> float:
    """Synchronous sentiment scoring."""
    pipeline = _get_pipeline()
    if pipeline == "fallback":
        return _lexicon_score(text)

    try:
        result = pipeline(text[:512])[0]
        label: str = result["label"]
        confidence: float = result["score"]
        # Map POSITIVE/NEGATIVE to [-1, 1]
        return confidence if label == "POSITIVE" else -confidence
    except Exception as exc:
        logger.warning("Sentiment pipeline error, using fallback", error=str(exc))
        return _lexicon_score(text)


async def score_sentiment(text: str) -> float:
    """
    Score sentiment of text, returning a float in [-1.0, 1.0].

    Runs in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _score_sync, text)


async def score_batch(texts: list[str]) -> list[float]:
    """Score sentiment for a batch of texts."""
    tasks = [score_sentiment(t) for t in texts]
    return await asyncio.gather(*tasks)
