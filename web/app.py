"""
Boter 2.0 - Web Dashboard Application
FastAPI app with Setup Wizard and Admin Dashboard
"""
import logging
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, Response
from telegram import Update

logger = logging.getLogger("boter.web")

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="Boter 2.0 Dashboard", docs_url=None, redoc_url=None)

# Mount static files
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Store bot app reference
_bot_app = None


def set_bot_app(bot_app):
    global _bot_app
    _bot_app = bot_app


# Include routes
from web.routes.setup import router as setup_router
from web.routes.dashboard import router as dashboard_router

app.include_router(setup_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    """Redirect to dashboard or setup"""
    from bot.core.config import load_bot_config
    config = await load_bot_config()
    if config and config.is_setup_complete:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/setup")


@app.post("/telegram-update")
async def telegram_webhook(request: Request):
    """Receive Telegram updates via Webhook"""
    global _bot_app
    if not _bot_app:
        return Response(status_code=503, content="Bot application is not running yet")
        
    try:
        data = await request.json()
        update = Update.de_json(data=data, bot=_bot_app.bot)
        await _bot_app.update_queue.put(update)
        return Response(status_code=200, content="OK")
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return Response(status_code=500, content="Internal Server Error")


async def start_web_server(bot_app=None):
    """Start the web server"""
    if bot_app:
        set_bot_app(bot_app)

    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8080"))

    config = uvicorn.Config(
        app, host=host, port=port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    await server.serve()
