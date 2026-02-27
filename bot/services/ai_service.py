"""
Vex - AI Provider Service
Dynamic, DB-driven AI cascade.
Reads providers from database (ordered by priority), tries them in order.

Supported provider types:
  - google_studio  → Google AI Studio (Gemini models)
  - blackbox       → Blackbox.ai (OpenAI-compatible endpoint)
  - huggingface    → Hugging Face Inference API (zero-shot classification)
"""
import logging
from datetime import date, datetime
from typing import Optional

from sqlalchemy import select, and_

from db.database import get_db
from db.models import AIProviderStat, AIProvider
from bot.core.config import get_ai_prompt_override

logger = logging.getLogger("vex.services.ai")

# Daily quota safety limits per type
DAILY_LIMITS: dict[str, int] = {
    "google_studio": 1450,
    "blackbox": 99999,      # No known hard limit; use credit balance
    "huggingface": 99999,   # No hard daily limit
}

# Keywords that indicate DAILY quota exhaustion (not just per-minute rate limit)
# These MUST be very specific to avoid false positives from invalid keys or network errors
DAILY_EXHAUSTION_KEYWORDS = [
    "quota exceeded for the day",
    "daily request quota",
    "daily quota",
    "you exceeded your current quota",
    "insufficient_quota",
]

# Only treat as daily exhaustion if ALSO contains one of these (double check)
DAILY_EXHAUSTION_CONFIRM = [
    "quota",
    "1500",
    "exceeded",
]

# Keywords for temporary (per-minute) rate limiting
MINUTE_RATE_KEYWORDS = ["429", "rate_limit", "rate limit", "too many requests"]

# Keywords for permanent errors (wrong key, region blocked, etc.) — do NOT skip until tomorrow
PERMANENT_ERROR_KEYWORDS = [
    "api_key_invalid", "invalid api key", "api key not valid",
    "permission_denied", "api_key_invalid",
    "not_found", "404",
]


# ─── DB Stats Helpers ─────────────────────────────────────────────────────────

async def _get_or_create_stat(session, provider_key: str, today: date) -> AIProviderStat:
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
    today = date.today()
    async with get_db() as session:
        stat = await _get_or_create_stat(session, provider_key, today)
        stat.requests_count += 1
        stat.last_status = status
        stat.last_error = error
        stat.last_used_at = datetime.utcnow()


async def _is_daily_quota_exhausted(provider_key: str, daily_limit: int) -> bool:
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
        if stat.last_status == "rate_limit_day":
            return True
        return stat.requests_count >= daily_limit


# ─── Provider Callers ─────────────────────────────────────────────────────────

async def _call_google_studio(api_key: str, model: str, text: str) -> float:
    """Call Google AI Studio (Gemini) API."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel(model or "gemini-1.5-flash")

    DEFAULT_PROMPT = (
        "أنت نظام كشف المحتوى المسيء في مجموعات التيليجرام. "
        "قيّم الرسالة التالية على مقياس من 0.0 إلى 1.0 حيث:\n"
        "- 0.0 = رسالة طبيعية تماماً\n"
        "- 1.0 = رسالة مسيئة جداً (شتم، تحرش، محتوى ضار)\n\n"
        "الرسالة: «{text}»\n\n"
        "أجب برقم عشري فقط بين 0.0 و 1.0، لا شيء آخر."
    )
    custom = await get_ai_prompt_override()
    prompt = (custom or DEFAULT_PROMPT).replace("{text}", text[:500])
    response = await gemini_model.generate_content_async(prompt)
    raw = response.text.strip().replace(",", ".")
    return max(0.0, min(1.0, float(raw.split()[0])))


async def _call_blackbox(api_key: str, model: str, text: str) -> float:
    """Call Blackbox.ai (OpenAI-compatible endpoint)."""
    import openai
    client = openai.AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.blackbox.ai",  # Correct base URL (no /api/v1)
    )
    DEFAULT_PROMPT = (
        "You are an Arabic content moderation system for Telegram groups. "
        "Rate the following message on a scale from 0.0 to 1.0 where:\n"
        "- 0.0 = completely normal message\n"
        "- 1.0 = highly abusive (insults, harassment, harmful content)\n\n"
        "Message: «{text}»\n\n"
        "Reply with ONLY a decimal number between 0.0 and 1.0, nothing else."
    )
    custom = await get_ai_prompt_override()
    prompt = (custom or DEFAULT_PROMPT).replace("{text}", text[:500])
    response = await client.chat.completions.create(
        model=model or "blackboxai",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
    )
    raw = response.choices[0].message.content.strip().replace(",", ".")
    return max(0.0, min(1.0, float(raw.split()[0])))


async def _call_huggingface(api_key: str, model: str, text: str) -> float:
    """Call HuggingFace Inference API with zero-shot classification."""
    import httpx
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": text[:1000],
        "parameters": {
            "candidate_labels": ["رسالة عادية", "رسالة مسيئة أو شتم أو تحرش"]
        },
    }
    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    labels = data.get("labels", [])
    scores = data.get("scores", [])
    target = "رسالة مسيئة أو شتم أو تحرش"
    if target in labels:
        return float(scores[labels.index(target)])
    return 0.0


# ─── Dispatch caller by type ──────────────────────────────────────────────────

async def _call_provider(provider: AIProvider, text: str) -> float:
    if provider.provider_type == "google_studio":
        return await _call_google_studio(provider.api_key, provider.model, text)
    elif provider.provider_type == "blackbox":
        return await _call_blackbox(provider.api_key, provider.model, text)
    elif provider.provider_type == "huggingface":
        return await _call_huggingface(provider.api_key, provider.model, text)
    raise ValueError(f"Unknown provider type: {provider.provider_type}")


# ─── Main Public Entry Point ──────────────────────────────────────────────────

async def analyze_text(text: str) -> float:
    """
    Run the full AI cascade using providers stored in the database.
    Returns a float 0.0–1.0 representing abuse probability.
    If all providers fail/exhausted, returns 0.0.
    """
    # Load all active providers sorted by priority
    async with get_db() as session:
        result = await session.execute(
            select(AIProvider)
            .where(AIProvider.is_active == True)
            .order_by(AIProvider.priority)
        )
        providers = list(result.scalars().all())

    if not providers:
        logger.warning("[AI] No active providers configured.")
        return 0.0

    for provider in providers:
        key_label = f"{provider.provider_type}:{provider.id}:{provider.name}"
        daily_limit = DAILY_LIMITS.get(provider.provider_type, 99999)

        # Skip if today's daily quota exhausted
        if await _is_daily_quota_exhausted(key_label, daily_limit):
            logger.info(f"[AI] '{provider.name}' daily quota exhausted, skipping.")
            continue

        try:
            score = await _call_provider(provider, text)
            await _record_usage(key_label, "ok")
            logger.info(f"[AI] '{provider.name}' → score={score:.2f}")
            return score

        except Exception as e:
            err_str = str(e).lower()

            # Permanent errors (wrong key, region blocked) → mark as error, try next
            if any(kw in err_str for kw in PERMANENT_ERROR_KEYWORDS):
                logger.error(f"[AI] '{provider.name}' permanent error (bad key?): {e}")
                await _record_usage(key_label, "error", f"[PERMANENT] {e}")
                continue

            # Daily quota exhausted → skip until tomorrow
            is_daily = (
                any(kw in err_str for kw in DAILY_EXHAUSTION_KEYWORDS)
                and any(kw in err_str for kw in DAILY_EXHAUSTION_CONFIRM)
            )
            if is_daily:
                logger.warning(f"[AI] '{provider.name}' daily quota hit.")
                await _record_usage(key_label, "rate_limit_day", str(e))
                continue

            # Per-minute rate limit → try next key immediately
            if any(kw in err_str for kw in MINUTE_RATE_KEYWORDS):
                logger.warning(f"[AI] '{provider.name}' minute rate limit, trying next.")
                await _record_usage(key_label, "rate_limit_minute", str(e))
                continue

            # Unknown error → log but try next
            logger.error(f"[AI] '{provider.name}' unknown error: {e}")
            await _record_usage(key_label, "error", str(e))
            continue

    logger.warning("[AI] All providers exhausted or failed. Returning 0.0.")
    return 0.0


# ─── Dashboard Stats Helper ───────────────────────────────────────────────────

async def get_provider_stats(days: int = 30) -> list[dict]:
    """Return usage stats for all providers for the last N days."""
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=days)

    async with get_db() as session:
        result = await session.execute(
            select(AIProviderStat)
            .where(AIProviderStat.stat_date >= cutoff)
            .order_by(AIProviderStat.stat_date.desc(), AIProviderStat.last_used_at.desc())
        )
        rows = result.scalars().all()

    return [
        {
            "id": r.id,
            "provider": r.provider_key,
            "date": r.stat_date.strftime("%Y-%m-%d"),
            "requests": r.requests_count,
            "status": r.last_status or "—",
            "last_used": r.last_used_at.strftime("%H:%M") if r.last_used_at else "—",
            "error": (r.last_error or "")[:300],
        }
        for r in rows
    ]


async def delete_provider_stat(stat_id: int) -> bool:
    """Delete a single AI provider stat row by its DB id."""
    async with get_db() as session:
        result = await session.execute(
            select(AIProviderStat).where(AIProviderStat.id == stat_id)
        )
        stat = result.scalar_one_or_none()
        if stat:
            await session.delete(stat)
            return True
        return False
