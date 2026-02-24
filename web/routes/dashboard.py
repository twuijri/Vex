"""
Vex - Dashboard Routes
Admin dashboard with stats and management
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os

from bot.core.config import load_bot_config
from bot.services.user_service import get_user_count, get_blocked_count, list_blocked_users
from bot.services.group_service import get_group_count, list_managed_groups
from bot.services.admin_service import list_admins

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

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "bot_username": config.bot_username,
        "user_count": user_count,
        "blocked_count": blocked_count,
        "group_count": group_count,
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
    })
