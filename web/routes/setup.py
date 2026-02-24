"""
Vex - Setup Wizard Routes
First-time configuration via web interface
"""
import logging

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import httpx

from bot.core.config import save_bot_config, load_bot_config

logger = logging.getLogger("vex.web.setup")

router = APIRouter(prefix="/setup", tags=["Setup"])
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


@router.get("/", response_class=HTMLResponse)
async def setup_page(request: Request):
    """Show setup wizard page"""
    config = await load_bot_config()
    if config and config.is_setup_complete:
        return RedirectResponse(url="/dashboard")

    return templates.TemplateResponse("setup.html", {
        "request": request,
        "error": None,
    })


@router.post("/", response_class=HTMLResponse)
async def setup_submit(
    request: Request,
    bot_token: str = Form(...),
    api_id: str = Form(...),
    api_hash: str = Form(...),
):
    """Process setup form submission"""
    errors = []

    # Validate bot token
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
            data = resp.json()
            if not data.get("ok"):
                errors.append("❌ Bot Token غير صالح")
            else:
                bot_username = data["result"]["username"]
    except Exception:
        errors.append("❌ لا يمكن التحقق من Bot Token")

    # Validate API ID
    try:
        api_id_int = int(api_id)
    except ValueError:
        errors.append("❌ API ID يجب أن يكون رقم")

    if not api_hash or len(api_hash) < 10:
        errors.append("❌ API Hash غير صالح")

    if errors:
        return templates.TemplateResponse("setup.html", {
            "request": request,
            "error": "\n".join(errors),
        })

    # Save configuration
    await save_bot_config(
        bot_token=bot_token,
        api_id=api_id_int,
        api_hash=api_hash,
        bot_username=bot_username,
    )

    return templates.TemplateResponse("setup_complete.html", {
        "request": request,
        "bot_username": bot_username,
    })
