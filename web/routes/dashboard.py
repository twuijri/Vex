"""
Vex - Dashboard Routes
Admin dashboard with stats and management
"""
import logging

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import httpx


from bot.services.user_service import get_user_count, get_blocked_count, list_blocked_users
from bot.services.group_service import (
    get_group_count, list_managed_groups,
    list_blocked_words_with_ids, delete_blocked_word_by_id,
    add_blocked_word, get_group_by_id,
)
from bot.services.admin_service import list_admins
from bot.services.ai_service import get_provider_stats, delete_provider_stat
from bot.services.ai_provider_service import (
    list_providers, add_provider, delete_provider, toggle_provider, move_provider,
)
from bot.core.config import (
    load_bot_config, get_ai_prompt_override, set_ai_prompt_override,
    get_ai_debug_channel_id, set_ai_debug_channel_id,
)

logger = logging.getLogger("vex.web.dashboard")

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Main dashboard with statistics"""
    config = await load_bot_config()
    if not config or not config.is_setup_complete:
        return RedirectResponse(url="/setup")

    user_count = await get_user_count()
    blocked_count = await get_blocked_count()
    group_count = await get_group_count()
    admins = await list_admins()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "bot_username": config.bot_username,
        "user_count": user_count,
        "blocked_count": blocked_count,
        "group_count": group_count,
        "admin_count": len(admins),
        "active_page": "dashboard",
    })


@router.get("/groups", response_class=HTMLResponse)
async def groups_page(request: Request):
    """Managed groups list"""
    config = await load_bot_config()
    if not config or not config.is_setup_complete:
        return RedirectResponse(url="/setup")

    groups = await list_managed_groups()

    return templates.TemplateResponse("groups.html", {
        "request": request,
        "groups": groups,
        "bot_username": config.bot_username,
            "active_page": "groups",
    })


@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """Users and blocked users"""
    config = await load_bot_config()
    if not config or not config.is_setup_complete:
        return RedirectResponse(url="/setup")

    blocked = await list_blocked_users()

    return templates.TemplateResponse("users.html", {
        "request": request,
        "blocked_users": blocked,
        "bot_username": config.bot_username,
            "active_page": "users",
    })


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """View bot application logs"""
    config = await load_bot_config()
    if not config or not config.is_setup_complete:
        return RedirectResponse(url="/setup")

    log_content = "لا توجد سجلات بعد (لم يتم إنشاء ملف السجل)."
    log_file = "vex.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                # Read last 1000 lines for performance
                lines = f.readlines()
                log_content = "".join(lines[-1000:])
        except Exception as e:
            log_content = f"خطأ في قراءة السجل: {e}"

    return templates.TemplateResponse("logs.html", {
        "request": request,
        "bot_username": config.bot_username,
        "logs": log_content,
            "active_page": "logs",
    })


@router.get("/ai-stats", response_class=HTMLResponse)
async def ai_stats_page(request: Request):
    """AI provider usage statistics dashboard"""
    config = await load_bot_config()
    if not config or not config.is_setup_complete:
        return RedirectResponse(url="/setup")

    stats = await get_provider_stats(days=30)

    # Build per-provider summary (today totals + 30-day totals)
    from datetime import date
    today_str = date.today().strftime("%Y-%m-%d")
    DAILY_LIMIT = 1450

    provider_labels = {
        "gemini_1": "Gemini Key 1",
        "gemini_2": "Gemini Key 2",
        "gemini_3": "Gemini Key 3",
        "huggingface": "HuggingFace",
    }

    totals: dict[str, dict] = {}
    for row in stats:
        key = row["provider"]
        if key not in totals:
            totals[key] = {"total": 0, "today": 0, "label": provider_labels.get(key, key)}
        totals[key]["total"] += row["requests"]
        if row["date"] == today_str:
            totals[key]["today"] += row["requests"]

    summaries = []
    for key, data in totals.items():
        limit = DAILY_LIMIT if "gemini" in key else None
        summaries.append({
            "label": data["label"],
            "total": data["total"],
            "today": data["today"],
            "limit": limit,
            "today_pct": round((data["today"] / limit) * 100) if limit else 0,
        })

    return templates.TemplateResponse("ai_stats.html", {
        "request": request,
        "bot_username": config.bot_username,
        "stats": stats,
        "summaries": summaries,
            "active_page": "ai_stats",
    })


@router.post("/ai-stats/{stat_id}/delete")
async def ai_stat_delete(stat_id: int):
    """Delete a single AI provider stat row"""
    await delete_provider_stat(stat_id)
    return RedirectResponse(url="/dashboard/ai-stats", status_code=303)

# ── Fetch available models for a provider key ────────────────────────────────

MODELS_ENDPOINTS = {
    "blackbox": "https://api.blackbox.ai/v1/models",
    "google_studio": None,   # Static list
    "huggingface": None,     # Static list
}

@router.get("/ai-providers/fetch-models")
async def fetch_provider_models(
    provider_type: str = Query(...),
    api_key: str = Query(...),
):
    """Fetch available model IDs for a given provider type and API key."""
    url = MODELS_ENDPOINTS.get(provider_type)
    if not url:
        return JSONResponse({"models": [], "error": "لا يدعم الجلب التلقائي"})
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
        models = [m.get("id", m) if isinstance(m, dict) else str(m)
                  for m in data.get("data", data.get("models", []))]
        return JSONResponse({"models": sorted(models)})
    except Exception as e:
        return JSONResponse({"models": [], "error": str(e)}, status_code=200)


# ── AI Provider Management ────────────────────────────────────────────────────

@router.get("/ai-providers", response_class=HTMLResponse)
async def ai_providers_page(request: Request):
    """AI provider management page"""
    config = await load_bot_config()
    if not config or not config.is_setup_complete:
        return RedirectResponse(url="/setup")

    providers = await list_providers()
    return templates.TemplateResponse("ai_providers.html", {
        "request": request,
        "bot_username": config.bot_username,
        "providers": providers,
            "active_page": "ai_providers",
    })


@router.post("/ai-providers/add")
async def ai_providers_add(
    request: Request,
    name: str = Form(...),
    provider_type: str = Form(...),
    api_key: str = Form(...),
    model: str = Form(...),
    priority: int = Form(10),
):
    """Add a new AI provider"""
    await add_provider(
        name=name,
        provider_type=provider_type,
        api_key=api_key,
        model=model,
        priority=priority,
    )
    return RedirectResponse(url="/dashboard/ai-providers", status_code=303)


@router.post("/ai-providers/{provider_id}/delete")
async def ai_providers_delete(provider_id: int):
    """Delete an AI provider"""
    await delete_provider(provider_id)
    return RedirectResponse(url="/dashboard/ai-providers", status_code=303)


@router.post("/ai-providers/{provider_id}/toggle")
async def ai_providers_toggle(provider_id: int):
    """Toggle an AI provider active/inactive"""
    await toggle_provider(provider_id)
    return RedirectResponse(url="/dashboard/ai-providers", status_code=303)


@router.post("/ai-providers/{provider_id}/move")
async def ai_providers_move(provider_id: int, direction: str = Form(...)):
    """Move a provider up or down in the cascade order"""
    await move_provider(provider_id, direction)
    return RedirectResponse(url="/dashboard/ai-providers", status_code=303)


# ── Per-Group Blocked Words Management ───────────────────────────────────────

@router.get("/groups/{group_id}/words", response_class=HTMLResponse)
async def group_words_page(request: Request, group_id: int, msg: str = ""):
    """Show and manage blocked words for a specific group"""
    config = await load_bot_config()
    if not config or not config.is_setup_complete:
        return RedirectResponse(url="/setup")

    group = await get_group_by_id(group_id)
    if not group:
        return RedirectResponse(url="/dashboard/groups")

    words = await list_blocked_words_with_ids(group_id)
    return templates.TemplateResponse("group_words.html", {
        "request": request,
        "bot_username": config.bot_username,
        "group": group,
        "words": words,
        "msg": msg,
            "active_page": "groups",
    })


@router.post("/groups/{group_id}/words/add")
async def group_words_add(group_id: int, word: str = Form(...)):
    """Add a blocked word to the group (duplicate-safe)"""
    group = await get_group_by_id(group_id)
    if not group:
        return RedirectResponse(url="/dashboard/groups", status_code=303)

    result_msg = await add_blocked_word(group.telegram_group_id, word.strip())
    return RedirectResponse(
        url=f"/dashboard/groups/{group_id}/words?msg={result_msg}",
        status_code=303,
    )


@router.post("/groups/{group_id}/words/{word_id}/delete")
async def group_words_delete(group_id: int, word_id: int):
    """Delete a blocked word by its DB id"""
    await delete_blocked_word_by_id(word_id)
    return RedirectResponse(
        url=f"/dashboard/groups/{group_id}/words",
        status_code=303,
    )


# ── AI Prompt Editor ──────────────────────────────────────────────────────────

# The default system instructions shown in the textarea (fixed suffix is added by code)
DEFAULT_PROMPT_REFERENCE = (
    "أنت نظام كشف المحتوى المسيء في مجموعات التيليجرام.\n"
    "قيّم الرسالة على مقياس من 0.0 إلى 1.0 حيث:\n"
    "- 0.0 = رسالة طبيعية تماماً\n"
    "- 1.0 = رسالة مسيئة جداً (شتم، تحرش، محتوى ضار)"
)


@router.get("/ai-prompt", response_class=HTMLResponse)
async def ai_prompt_page(request: Request, msg: str = ""):
    config = await load_bot_config()
    if not config or not config.is_setup_complete:
        return RedirectResponse(url="/setup")
    providers = await list_providers()
    current = await get_ai_prompt_override()
    debug_ch = await get_ai_debug_channel_id()
    return templates.TemplateResponse("ai_prompt.html", {
        "request": request,
        "bot_username": config.bot_username,
        "has_providers": bool(providers),
        "current_prompt": current or DEFAULT_PROMPT_REFERENCE,
        "default_prompt": DEFAULT_PROMPT_REFERENCE,
        "debug_channel_id": debug_ch,
        "msg": msg,
            "active_page": "ai_prompt",
    })


@router.post("/ai-prompt/save")
async def ai_prompt_save(prompt: str = Form(...)):
    await set_ai_prompt_override(prompt.strip() or None)
    return RedirectResponse(url="/dashboard/ai-prompt?msg=تم حفظ البرومبت بنجاح ✅", status_code=303)


@router.post("/ai-prompt/reset")
async def ai_prompt_reset():
    await set_ai_prompt_override(None)
    return RedirectResponse(url="/dashboard/ai-prompt?msg=تمت إعادة الضبط إلى الافتراضي ✅", status_code=303)


@router.post("/ai-prompt/debug-channel/save")
async def ai_debug_channel_save(channel_id: str = Form(...)):
    """Save the debug channel ID (numeric or @username)"""
    raw = channel_id.strip()
    try:
        cid = int(raw)
    except ValueError:
        cid = None  # Let the bot handle @username resolution
        # Store as string representation for now — convert on first use
        await set_ai_debug_channel_id(None)
        return RedirectResponse(url="/dashboard/ai-prompt?msg=أدخل معرفاً رقمياً (مثال: -100123456789)", status_code=303)
    await set_ai_debug_channel_id(cid)
    return RedirectResponse(url="/dashboard/ai-prompt?msg=تم حفظ قناة التتبع ✅", status_code=303)


@router.post("/ai-prompt/debug-channel/clear")
async def ai_debug_channel_clear():
    """Disable the debug channel"""
    await set_ai_debug_channel_id(None)
    return RedirectResponse(url="/dashboard/ai-prompt?msg=تم إيقاف قناة التتبع ✅", status_code=303)
