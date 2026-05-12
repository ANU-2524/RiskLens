"""Gemini API integration for AI-powered risk summaries (previously Claude)."""

import json
import time
from typing import Any, Dict, List, Optional

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Simple in-memory rate limiter
_call_timestamps: List[float] = []

RiskLens_SYSTEM_PROMPT = """You are RiskLens, an AI-powered global business risk intelligence system.
Your role is to analyse risk signals for companies, countries, and sectors and provide
clear, actionable intelligence to decision-makers at major corporations and financial institutions.

You communicate with precision and authority. Your summaries are concise, evidence-based,
and immediately actionable. You never speculate without data. You always cite the signals
that drove your assessment."""


def _check_rate_limit() -> bool:
    """Return True if we are within the hourly Gemini call limit."""
    now = time.time()
    cutoff = now - 3600  # 1 hour window
    global _call_timestamps
    _call_timestamps = [t for t in _call_timestamps if t > cutoff]
    return len(_call_timestamps) < settings.claude_rate_limit_per_hour


def _record_call() -> None:
    """Record a Gemini API call timestamp."""
    _call_timestamps.append(time.time())


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def generate_risk_summary(
    entity_name: str,
    entity_type: str,
    risk_score: float,
    signals: List[Dict[str, Any]],
    sector: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call Gemini API to generate a structured risk summary for a high-risk entity.

    Returns a dict with: summary_text, severity, contributing_signals, recommended_action, prompt_used.
    """
    if not _check_rate_limit():
        logger.warning("Gemini rate limit reached, skipping AI summary", entity=entity_name)
        return _fallback_summary(entity_name, risk_score)

    if not settings.google_api_key:
        logger.warning("No Google API key configured, using fallback summary")
        return _fallback_summary(entity_name, risk_score)

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=RiskLens_SYSTEM_PROMPT
        )
    except ImportError:
        logger.error("google-generativeai package not installed")
        return _fallback_summary(entity_name, risk_score)

    # Build signal context
    signal_context = "\n".join(
        f"- [{s.get('signal_type', 'unknown').upper()}] {s.get('source', 'unknown')}: "
        f"sentiment={s.get('sentiment_score', 0):.2f} | {s.get('raw_text', '')[:200]}"
        for s in signals[:10]
    )

    prompt = f"""Analyse the following risk signals for {entity_name} ({entity_type}{f', {sector} sector' if sector else ''}).

Current Risk Score: {risk_score:.1f}/100

Recent Signals:
{signal_context}

Provide a structured risk assessment in the following JSON format:
{{
  "summary": "3-sentence plain-English risk summary explaining what is happening and why it matters",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "contributing_signals": [
    {{"signal": "description of signal 1", "evidence": "specific data point"}},
    {{"signal": "description of signal 2", "evidence": "specific data point"}},
    {{"signal": "description of signal 3", "evidence": "specific data point"}}
  ],
  "recommended_action": "Specific action decision-makers should take right now"
}}

Respond with valid JSON only."""

    _record_call()

    try:
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=settings.claude_max_tokens,
                temperature=0.1,
            )
        )

        content = response.text.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            if content.endswith("```"):
                 content = content[:-3]

        parsed = json.loads(content)
        return {
            "summary_text": parsed.get("summary", ""),
            "severity": parsed.get("severity", "MEDIUM"),
            "contributing_signals": parsed.get("contributing_signals", []),
            "recommended_action": parsed.get("recommended_action", ""),
            "prompt_used": prompt,
        }

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON response", error=str(exc))
        return _fallback_summary(entity_name, risk_score)
    except Exception as exc:
        logger.error("Gemini API call failed", error=str(exc))
        return _fallback_summary(entity_name, risk_score)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def answer_natural_language_query(
    question: str,
    context: str,
) -> str:
    """
    Answer a natural language risk intelligence question using Gemini.

    Returns a plain-text answer string.
    """
    if not _check_rate_limit():
        return "Rate limit reached. Please try again in a few minutes."

    if not settings.google_api_key:
        return _fallback_query_answer(question)

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=RiskLens_SYSTEM_PROMPT
        )
    except ImportError:
        return _fallback_query_answer(question)

    prompt = f"""Using the following live risk intelligence data, answer this question:

Question: {question}

Current Risk Intelligence Context:
{context}

Provide a clear, concise answer (2-4 sentences) based only on the data provided.
If the data does not contain enough information to answer, say so clearly."""

    _record_call()

    try:
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.1,
            )
        )
        return response.text.strip()
    except Exception as exc:
        logger.error("Gemini query failed", error=str(exc))
        return f"Unable to process query at this time. Error: {str(exc)}"


def _fallback_summary(entity_name: str, risk_score: float) -> Dict[str, Any]:
    """Generate a rule-based fallback summary when AI is unavailable."""
    if risk_score >= 80:
        severity = "CRITICAL"
        summary = (
            f"{entity_name} is showing critical risk indicators across multiple signal sources. "
            f"Anomalous patterns in sentiment, volume, and market data suggest an elevated probability "
            f"of adverse events. Immediate attention from risk management teams is warranted."
        )
        action = "Escalate to senior risk committee immediately. Consider reducing exposure."
    elif risk_score >= 60:
        severity = "HIGH"
        summary = (
            f"{entity_name} has triggered high-risk thresholds based on recent signal analysis. "
            f"Negative sentiment trends and unusual activity patterns have been detected. "
            f"Close monitoring and contingency planning are recommended."
        )
        action = "Increase monitoring frequency. Prepare contingency plans."
    elif risk_score >= 35:
        severity = "MEDIUM"
        summary = (
            f"{entity_name} shows moderate risk signals that warrant attention. "
            f"Some negative indicators have been detected but have not yet reached critical levels. "
            f"Standard monitoring protocols should be maintained with heightened awareness."
        )
        action = "Monitor closely. Review exposure levels."
    else:
        severity = "LOW"
        summary = (
            f"{entity_name} currently shows low risk indicators across monitored signals. "
            f"Sentiment and market data remain within normal parameters. "
            f"Routine monitoring is sufficient at this time."
        )
        action = "Continue standard monitoring protocols."

    return {
        "summary_text": summary,
        "severity": severity,
        "contributing_signals": [
            {"signal": "Sentiment analysis", "evidence": f"Risk score: {risk_score:.1f}/100"},
            {"signal": "Volume anomaly detection", "evidence": "Automated signal analysis"},
            {"signal": "Market data correlation", "evidence": "Cross-source pattern matching"},
        ],
        "recommended_action": action,
        "prompt_used": None,
    }


def _fallback_query_answer(question: str) -> str:
    """Fallback answer when Claude is unavailable."""
    return (
        "RiskLens AI query processing is currently unavailable. "
        "Please check your API configuration and try again. "
        f"Your question was: '{question}'"
    )

