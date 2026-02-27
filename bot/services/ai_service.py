"""
Vex - AI Provider Service
Multi-key cascade: Gemini API keys (1→2→3) → HuggingFace fallback.

Smart logic:
- If a key hit its DAILY quota → skip it entirely until tomorrow
- If a key hit only MINUTE rate limit → try next key immediately
- Tracks all requests in DB for dashboard reporting
"""
import logging
import os
from datetime import date, datetime
from typing import Optional

from sqlalchemy import select, and_

from db.database import get_db
from db.models import AIProviderStat

logger = logging.getLogger("vex.services.ai")

# ─── AI Config ────────────────────────────────────────────────────────────────
GEMINI_KEYS: list[str] = [
    k for k in [
        os.getenv("GEMINI_KEY_1"),
        os.getenv("GEMINI_KEY_2"),
        os.getenv("GEMINI_KEY_3"),
    ] if k  # only include keys that are actually set
]
HUGGINGFACE_KEY: Optional[str] = os.getenv("HUGGINGFACE_KEY")
HF_MODEL: str = os.getenv("HF_MODEL", "aubmindlab/bert-base-arabertv02")

DAILY_QUOTA_LIMIT: int = 1450  # Use 1450 as safe buffer below the 1500/day limit
AI_SCORE_THRESHOLD: float = 0.80

# Keywords detected in error messages indicating daily quota exhaustion
DAILY_EXHAUSTION_KEYWORDS = [
    "quota exceeded",
    "daily quota",
    "resource has been exhausted",
]


# ─── DB Helpers ───────────────────────────────────────────────────────────────

async def _get_or_create_stat(session, provider_key: str, today: date) -> AIProviderStat:
    """Get or create today's stat row for a provider."""
    result = await session.execute(
        select(AIProviderStat).where(
            and_(
                AIProviderStat.provider_key == provider_key,
                AIProviderStat.stat_date == today,
            )
        )
    )
    stat = result.scalar_one_or_none()
    if not stat:
        stat = AIProviderStat(
            provider_key=provider_key,
            stat_date=today,
            requests_count=0,
        )
        session.add(stat)
        await session.flush()
    return stat


async def _record_usage(provider_key: str, status: str, error: Optional[str] = None):
    """Increment request counter and record status for a provider."""
    today = date.today()
    async with get_db() as session:
        stat = await _get_or_create_stat(session, provider_key, today)
        stat.requests_count += 1
        stat.last_status = status
        stat.last_error = error
        stat.last_used_at = datetime.utcnow()


async def _is_daily_quota_exhausted(provider_key: str) -> bool:
    """Return True if today's count has reached the daily safe limit."""
    today = date.today()
    async with get_db() as session:
        result = await session.execute(
            select(AIProviderStat).where(
                and_(
                    AIProviderStat.provider_key == provider_key,
                    AIProviderStat.stat_date == today,
                )
            )
        )
        stat = result.scalar_one_or_none()
        if not stat:
            return False
        # Also checks if last call resulted in a daily exhaustion error
        if stat.last_status == "rate_limit_day":
            return True
        return stat.requests_count >= DAILY_QUOTA_LIMIT


# ─── Gemini Caller ────────────────────────────────────────────────────────────

async def _call_gemini(api_key: str, text: str) -> float:
    """
    Call Gemini API to classify text as abusive.
    Returns float 0.0–1.0 or raises an exception on failure.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = (
        "أنت نظام كشف المحتوى المسيء في مجموعات التيليجرام. "
        "قيّم الرسالة التالية على مقياس من 0.0 إلى 1.0 حيث:\n"
        "- 0.0 = رسالة طبيعية تماماً\n"
        "- 1.0 = رسالة مسيئة جداً أو تحرش أو شتم\n\n"
        "الرسالة: «{}»\n\n"
        "أجب برقم عشري فقط بين 0.0 و 1.0، لا شيء آخر."
    ).format(text[:500])

    response = await model.generate_content_async(prompt)
    raw = response.text.strip().replace(",", ".")

    # Parse the numeric score
    score = float(raw.split()[0])
    return max(0.0, min(1.0, score))


# ─── HuggingFace Caller ───────────────────────────────────────────────────────

async def _call_huggingface(text: str) -> float:
    """
    Call HuggingFace Inference API using a zero-shot classifier.
    Returns float 0.0–1.0 representing abuse probability.
    """
    import httpx

    if not HUGGINGFACE_KEY:
        raise RuntimeError("HUGGINGFACE_KEY not set")

    url = f"https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_KEY}"}
    payload = {
        "inputs": text[:1000],
        "parameters": {
            "candidate_labels": ["رسالة عادية", "رسالة مسيئة أو شتم أو تحرش"]
        }
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # data = {"labels": [...], "scores": [...]}
    labels = data.get("labels", [])
    scores = data.get("scores", [])
    if "رسالة مسيئة أو شتم أو تحرش" in labels:
        idx = labels.index("رسالة مسيئة أو شتم أو تحرش")
        return float(scores[idx])
    return 0.0


# ─── Public Entry Point ───────────────────────────────────────────────────────

async def analyze_text(text: str) -> float:
    """
    Run the full AI cascade:
    Gemini Key 1 → Gemini Key 2 → Gemini Key 3 → HuggingFace → 0.0 (skip)

    Returns a float 0.0–1.0 representing the abuse probability.
    """
    # ── Gemini Keys ──────────────────────────────────────────────────────────
    for idx, key in enumerate(GEMINI_KEYS, start=1):
        provider_name = f"gemini_{idx}"

        # Skip if today's quota is already exhausted
        if await _is_daily_quota_exhausted(provider_name):
            logger.info(f"[AI] {provider_name} daily quota exhausted, skipping.")
            continue

        try:
            score = await _call_gemini(key, text)
            await _record_usage(provider_name, "ok")
            logger.info(f"[AI] {provider_name} → score={score:.2f}")
            return score

        except Exception as e:
            err_str = str(e).lower()

            # Detect daily quota error
            if any(kw in err_str for kw in DAILY_EXHAUSTION_KEYWORDS):
                logger.warning(f"[AI] {provider_name} daily quota hit. Marking exhausted.")
                await _record_usage(provider_name, "rate_limit_day", str(e))
                continue  # Try next key

            # Detect minute rate limit (try next key)
            if "429" in err_str or "rate" in err_str:
                logger.warning(f"[AI] {provider_name} minute rate limit. Trying next.")
                await _record_usage(provider_name, "rate_limit_minute", str(e))
                continue

            # Other errors (network, invalid key, etc.)
            logger.error(f"[AI] {provider_name} error: {e}")
            await _record_usage(provider_name, "error", str(e))
            continue  # Try next key

    # ── HuggingFace Fallback ─────────────────────────────────────────────────
    if HUGGINGFACE_KEY:
        if not await _is_daily_quota_exhausted("huggingface"):
            try:
                score = await _call_huggingface(text)
                await _record_usage("huggingface", "ok")
                logger.info(f"[AI] huggingface → score={score:.2f}")
                return score
            except Exception as e:
                err_str = str(e).lower()
                status = "rate_limit_day" if "quota" in err_str else "error"
                logger.error(f"[AI] huggingface error: {e}")
                await _record_usage("huggingface", status, str(e))

    # ── All providers failed/exhausted ───────────────────────────────────────
    logger.warning("[AI] All AI providers failed or exhausted. Returning 0.0.")
    return 0.0


# ─── Dashboard Data Helper ────────────────────────────────────────────────────

async def get_provider_stats(days: int = 30) -> list[dict]:
    """
    Return usage stats for all providers for the last N days.
    Returns list of dicts for the dashboard template.
    """
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=days)

    async with get_db() as session:
        result = await session.execute(
            select(AIProviderStat)
            .where(AIProviderStat.stat_date >= cutoff)
            .order_by(AIProviderStat.provider_key, AIProviderStat.stat_date.desc())
        )
        rows = result.scalars().all()

    return [
        {
            "provider": r.provider_key,
            "date": r.stat_date.strftime("%Y-%m-%d"),
            "requests": r.requests_count,
            "status": r.last_status or "—",
            "last_used": r.last_used_at.strftime("%H:%M") if r.last_used_at else "—",
        }
        for r in rows
    ]
