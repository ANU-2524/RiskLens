"""Named Entity Recognition using spaCy."""

import asyncio
from typing import Dict, List

import structlog

logger = structlog.get_logger(__name__)

# Lazy-load spaCy model to avoid startup delay
_nlp = None


def _get_nlp():
    """Load spaCy model lazily."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using blank model")
            import spacy
            _nlp = spacy.blank("en")
    return _nlp


async def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities from text using spaCy.

    Returns a dict with entity types as keys and lists of entity strings as values.
    Runs in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_entities_sync, text)


def _extract_entities_sync(text: str) -> Dict[str, List[str]]:
    """Synchronous NER extraction."""
    nlp = _get_nlp()
    doc = nlp(text[:10000])  # Limit text length for performance

    entities: Dict[str, List[str]] = {
        "companies": [],
        "countries": [],
        "people": [],
        "sectors": [],
        "misc": [],
    }

    seen: set = set()
    for ent in doc.ents:
        key = ent.text.strip()
        if key in seen or len(key) < 2:
            continue
        seen.add(key)

        if ent.label_ in ("ORG",):
            entities["companies"].append(key)
        elif ent.label_ in ("GPE", "LOC"):
            entities["countries"].append(key)
        elif ent.label_ in ("PERSON",):
            entities["people"].append(key)
        else:
            entities["misc"].append(key)

    return entities


# Known sector keywords for simple sector tagging
SECTOR_KEYWORDS: Dict[str, List[str]] = {
    "Finance": ["bank", "financial", "investment", "hedge fund", "insurance", "credit", "loan"],
    "Technology": ["tech", "software", "cloud", "ai", "semiconductor", "chip", "data center"],
    "Energy": ["oil", "gas", "energy", "petroleum", "renewable", "solar", "wind", "coal"],
    "Retail": ["retail", "consumer", "store", "e-commerce", "shopping", "merchandise"],
    "Healthcare": ["pharma", "biotech", "hospital", "drug", "medical", "health", "vaccine"],
    "Real Estate": ["real estate", "property", "reit", "housing", "mortgage", "construction"],
    "Crypto": ["crypto", "bitcoin", "ethereum", "blockchain", "defi", "exchange", "token"],
}


def infer_sector(text: str) -> str:
    """Infer sector from text using keyword matching."""
    text_lower = text.lower()
    scores: Dict[str, int] = {}
    for sector, keywords in SECTOR_KEYWORDS.items():
        scores[sector] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=lambda s: scores[s])
    return best if scores[best] > 0 else "General"
