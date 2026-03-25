"""
Vex - Auth Routes (login / logout)
"""
import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from web.auth import (
    get_dashboard_password, create_auth_token,
    set_auth_cookie, clear_auth_cookie, verify_auth_token,
)

router = APIRouter(prefix="/dashboard", tags=["Auth"])
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    # Already logged in → go to dashboard
    token = request.cookies.get("vex_auth", "")
    if token and verify_auth_token(token):
        return RedirectResponse(url="/dashboard/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@router.post("/login")
async def login_submit(password: str = Form(...)):
    if password == get_dashboard_password():
        token = create_auth_token()
        response = RedirectResponse(url="/dashboard/", status_code=302)
        set_auth_cookie(response, token)
        return response
    response = RedirectResponse(url="/dashboard/login?error=كلمة المرور غير صحيحة", status_code=302)
    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/dashboard/login", status_code=302)
    clear_auth_cookie(response)
    return response
