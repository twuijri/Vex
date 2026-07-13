"""
Vex - JSON API for the React dashboard (SPA)
All endpoints live under /api and are guarded by the auth middleware
(401 JSON instead of redirects). Login/logout manage the same signed cookie
used previously by the Jinja dashboard.
"""
import logging
import os

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel

from web.auth import (
    get_dashboard_password, create_auth_token,
    set_auth_cookie, clear_auth_cookie,
)
from bot.services.user_service import get_user_count, get_blocked_count, list_blocked_users
from bot.services.group_service import (
    get_group_count, list_managed_groups, activate_group,
    list_blocked_words_with_ids, delete_blocked_word_by_id,
    add_blocked_word, get_group_by_id,
)
from bot.services.admin_service import get_admin_count
from bot.services.ai_service import get_provider_stats, delete_provider_stat
from bot.services.ai_provider_service import (
    list_providers, add_provider, delete_provider, toggle_provider,
    reorder_providers,
    list_endpoints, get_endpoint, add_endpoint, update_endpoint, delete_endpoint,
)
from bot.core.config import (
    load_bot_config, get_ai_prompt_override, set_ai_prompt_override,
    get_ai_debug_channel_id, set_ai_debug_channel_id,
    get_ai_thresholds, set_ai_thresholds,
)

logger = logging.getLogger("vex.web.api")

router = APIRouter(prefix="/api", tags=["API"])

# Prompt display constants (mirror ai_service.py)
FIXED_PREFIX_DISPLAY = (
    "أنت نظام مراقبة محتوى لمجموعات تيليجرام. "
    "مهمتك تقييم الرسائل على مقياس من 0.0 إلى 1.0 حيث:\n"
    "  • 0.0 = رسالة طبيعية تماماً\n"
    "  • 1.0 = رسالة مسيئة جداً\n\n"
    "قواعد المجموعة:"
)
FIXED_SUFFIX_DISPLAY = (
    "الرسالة: «نص الرسالة»\n"
    "أجب برقم عشري فقط بين 0.0 و 1.0، لا شيء آخر."
)
DEFAULT_RULES_REFERENCE = (
    "- الشتائم والألفاظ النابية\n"
    "- التحرش والمحتوى الجنسي\n"
    "- التهديد والعنف\n"
    "- العنصرية والتمييز\n"
    "- الإزعاج المتكرر والسبام"
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginBody(BaseModel):
    password: str


@router.post("/login")
async def api_login(body: LoginBody):
    if body.password == get_dashboard_password():
        resp = JSONResponse({"ok": True})
        set_auth_cookie(resp, create_auth_token())
        return resp
    return JSONResponse({"ok": False, "error": "كلمة المرور غير صحيحة"}, status_code=401)


@router.post("/logout")
async def api_logout():
    resp = JSONResponse({"ok": True})
    clear_auth_cookie(resp)
    return resp


@router.get("/me")
async def api_me():
    """Reached only when authed (middleware guards it). Returns app context."""
    config = await load_bot_config()
    return {
        "ok": True,
        "bot_username": config.bot_username if config else None,
        "setup_complete": bool(config and config.is_setup_complete),
    }


# ── Overview ──────────────────────────────────────────────────────────────────

@router.get("/overview")
async def api_overview():
    return {
        "users": await get_user_count(),
        "blocked": await get_blocked_count(),
        "groups": await get_group_count(),
        "admins": await get_admin_count(),
    }


# ── Groups & blocked words ────────────────────────────────────────────────────

@router.get("/groups")
async def api_groups():
    groups = await list_managed_groups()
    return [
        {
            "id": g.id,
            "telegram_group_id": g.telegram_group_id,
            "name": g.group_name,
            "type": g.group_type,
            "is_active": g.is_active,
            "activated_at": g.activated_at.isoformat() if g.activated_at else None,
        }
        for g in groups
    ]


class GroupAddBody(BaseModel):
    telegram_group_id: str
    group_name: str


@router.post("/groups")
async def api_groups_add(body: GroupAddBody):
    try:
        gid = int(body.telegram_group_id.strip())
    except ValueError:
        return JSONResponse({"ok": False, "error": "ID غير صحيح، تأكد أنه رقم"}, status_code=400)
    result = await activate_group(
        telegram_group_id=gid,
        group_name=body.group_name.strip(),
        group_type="group",
        activated_by=0,
    )
    return {"ok": True, "message": result}


@router.get("/groups/{group_id}/words")
async def api_group_words(group_id: int):
    group = await get_group_by_id(group_id)
    if not group:
        return JSONResponse({"ok": False, "error": "المجموعة غير موجودة"}, status_code=404)
    words = await list_blocked_words_with_ids(group_id)
    return {"group": {"id": group.id, "name": group.group_name}, "words": words}


class WordBody(BaseModel):
    word: str


@router.post("/groups/{group_id}/words")
async def api_group_words_add(group_id: int, body: WordBody):
    group = await get_group_by_id(group_id)
    if not group:
        return JSONResponse({"ok": False, "error": "المجموعة غير موجودة"}, status_code=404)
    msg = await add_blocked_word(group.telegram_group_id, body.word.strip())
    return {"ok": True, "message": msg}


@router.delete("/groups/{group_id}/words/{word_id}")
async def api_group_words_delete(group_id: int, word_id: int):
    await delete_blocked_word_by_id(word_id)
    return {"ok": True}


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users/blocked")
async def api_blocked_users():
    blocked = await list_blocked_users()
    return [
        {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "username": u.username,
            "blocked_at": u.blocked_at.isoformat() if u.blocked_at else None,
        }
        for u in blocked
    ]


# ── AI Endpoints (saved connections) ─────────────────────────────────────────

def _endpoint_json(ep, model_count: int = 0):
    return {
        "id": ep.id,
        "name": ep.name,
        "provider_type": ep.provider_type,
        "base_url": ep.base_url,
        "key_hint": ("****" + ep.api_key[-4:]) if ep.api_key else None,
        "model_count": model_count,
    }


@router.get("/endpoints")
async def api_endpoints():
    items = await list_endpoints()
    return [_endpoint_json(i["endpoint"], i["model_count"]) for i in items]


class EndpointBody(BaseModel):
    name: str
    provider_type: str = "litellm"
    api_key: str = ""
    base_url: str = ""


@router.post("/endpoints")
async def api_endpoints_add(body: EndpointBody):
    ep = await add_endpoint(
        name=body.name,
        provider_type=body.provider_type,
        api_key=body.api_key,
        base_url=body.base_url.strip() or None,
    )
    return {"ok": True, "endpoint": _endpoint_json(ep)}


class EndpointUpdateBody(BaseModel):
    name: str = ""
    api_key: str = ""
    base_url: str = ""


@router.patch("/endpoints/{endpoint_id}")
async def api_endpoints_update(endpoint_id: int, body: EndpointUpdateBody):
    ok = await update_endpoint(
        endpoint_id,
        name=body.name or None,
        api_key=body.api_key or None,
        base_url=body.base_url,
    )
    if not ok:
        return JSONResponse({"ok": False, "error": "المزود غير موجود"}, status_code=404)
    return {"ok": True}


@router.delete("/endpoints/{endpoint_id}")
async def api_endpoints_delete(endpoint_id: int):
    await delete_endpoint(endpoint_id)
    return {"ok": True}


@router.get("/endpoints/{endpoint_id}/models")
async def api_endpoint_fetch_models(endpoint_id: int):
    """Fetch available model IDs from the remote provider."""
    endpoint = await get_endpoint(endpoint_id)
    if not endpoint:
        return JSONResponse({"models": [], "error": "المزود غير موجود"}, status_code=404)

    provider_type = endpoint.provider_type
    api_key = endpoint.api_key or ""
    base_url = (endpoint.base_url or "").rstrip("/")

    if provider_type == "litellm":
        if not base_url:
            return {"models": [], "error": "المزود لا يحتوي على رابط سيرفر"}
        url = base_url if base_url.endswith("/v1") else base_url + "/v1"
        url += "/models"
    elif provider_type == "blackbox":
        url = "https://api.blackbox.ai/v1/models"
    else:
        return {"models": [], "error": "هذا النوع لا يدعم الجلب التلقائي"}

    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        models = [m.get("id", m) if isinstance(m, dict) else str(m)
                  for m in data.get("data", data.get("models", []))]
        return {"models": sorted(models)}
    except Exception as e:
        return {"models": [], "error": str(e)}


# ── AI Models (cascade) ───────────────────────────────────────────────────────

def _model_json(p):
    ep = getattr(p, "endpoint", None)
    return {
        "id": p.id,
        "name": p.name,
        "model": p.model,
        "provider_type": p.provider_type,
        "priority": p.priority,
        "is_active": p.is_active,
        "endpoint_id": p.endpoint_id,
        "endpoint_name": ep.name if ep else None,
    }


@router.get("/models")
async def api_models():
    providers = await list_providers()
    return [_model_json(p) for p in providers]


class ModelBody(BaseModel):
    endpoint_id: int
    model: str
    name: str = ""
    priority: int = 10


@router.post("/models")
async def api_models_add(body: ModelBody):
    provider = await add_provider(
        name=body.name.strip() or body.model,
        endpoint_id=body.endpoint_id,
        model=body.model,
        priority=body.priority,
    )
    if not provider:
        return JSONResponse({"ok": False, "error": "المزود المحدد غير موجود"}, status_code=400)
    return {"ok": True, "model": _model_json(provider)}


@router.delete("/models/{model_id}")
async def api_models_delete(model_id: int):
    await delete_provider(model_id)
    return {"ok": True}


@router.post("/models/{model_id}/toggle")
async def api_models_toggle(model_id: int):
    state = await toggle_provider(model_id)
    if state is None:
        return JSONResponse({"ok": False, "error": "الموديل غير موجود"}, status_code=404)
    return {"ok": True, "is_active": state}


class ReorderBody(BaseModel):
    ids: list[int]


@router.post("/models/reorder")
async def api_models_reorder(body: ReorderBody):
    """Set cascade order from a drag-and-drop sorted list of model ids."""
    await reorder_providers(body.ids)
    return {"ok": True}


# ── AI Stats ──────────────────────────────────────────────────────────────────

@router.get("/ai-stats")
async def api_ai_stats(days: int = Query(30, ge=1, le=90)):
    from datetime import date
    stats = await get_provider_stats(days=days)
    today_str = date.today().strftime("%Y-%m-%d")

    totals: dict[str, dict] = {}
    for row in stats:
        key = row["provider"]
        if key not in totals:
            totals[key] = {"label": key, "total": 0, "today": 0}
        totals[key]["total"] += row["requests"]
        if row["date"] == today_str:
            totals[key]["today"] += row["requests"]

    return {"stats": stats, "summaries": list(totals.values())}


@router.delete("/ai-stats/{stat_id}")
async def api_ai_stats_delete(stat_id: int):
    await delete_provider_stat(stat_id)
    return {"ok": True}


# ── AI Prompt & thresholds ────────────────────────────────────────────────────

@router.get("/prompt")
async def api_prompt():
    providers = await list_providers()
    current = await get_ai_prompt_override()
    debug_ch = await get_ai_debug_channel_id()
    alert_thr, auto_del_thr = await get_ai_thresholds()
    return {
        "has_providers": bool(providers),
        "current_rules": current or "",
        "default_rules": DEFAULT_RULES_REFERENCE,
        "fixed_prefix": FIXED_PREFIX_DISPLAY,
        "fixed_suffix": FIXED_SUFFIX_DISPLAY,
        "debug_channel_id": debug_ch,
        "alert_threshold": alert_thr,
        "auto_delete_threshold": auto_del_thr,
    }


class PromptBody(BaseModel):
    prompt: str


@router.post("/prompt")
async def api_prompt_save(body: PromptBody):
    await set_ai_prompt_override(body.prompt.strip() or None)
    return {"ok": True, "message": "تم حفظ البرومبت بنجاح"}


@router.post("/prompt/reset")
async def api_prompt_reset():
    await set_ai_prompt_override(None)
    return {"ok": True, "message": "تمت إعادة الضبط إلى الافتراضي"}


class ThresholdsBody(BaseModel):
    alert_threshold: float
    auto_delete_threshold: float


@router.post("/thresholds")
async def api_thresholds_save(body: ThresholdsBody):
    if body.alert_threshold >= body.auto_delete_threshold:
        return JSONResponse(
            {"ok": False, "error": "عتبة التنبيه يجب أن تكون أقل من عتبة الحذف التلقائي"},
            status_code=400,
        )
    await set_ai_thresholds(body.alert_threshold, body.auto_delete_threshold)
    return {"ok": True, "message": "تم حفظ العتبات بنجاح"}


class DebugChannelBody(BaseModel):
    channel_id: str = ""


@router.post("/debug-channel")
async def api_debug_channel_save(body: DebugChannelBody):
    raw = body.channel_id.strip()
    if not raw:
        await set_ai_debug_channel_id(None)
        return {"ok": True, "message": "تم إيقاف قناة التتبع"}
    try:
        cid = int(raw)
    except ValueError:
        return JSONResponse(
            {"ok": False, "error": "أدخل معرفاً رقمياً (مثال: -100123456789)"},
            status_code=400,
        )
    await set_ai_debug_channel_id(cid)
    return {"ok": True, "message": "تم حفظ قناة التتبع"}


# ── Logs ──────────────────────────────────────────────────────────────────────

@router.get("/logs")
async def api_logs(lines: int = Query(500, ge=10, le=3000)):
    log_file = "vex.log"
    content = ""
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = "".join(f.readlines()[-lines:])
        except Exception as e:
            content = f"خطأ في قراءة السجل: {e}"
    return {"content": content}
