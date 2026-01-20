from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import setup
from backend.database.local_db import get_system_config

# ==============================================================================
# 📄 File: backend/main.py
# 📝 Description: Main application entry point for FastAPI.
# 📝 الوصف: نقطة الدخول الرئيسية لـ FastAPI (الواجهة الخلفية).
# ==============================================================================

app = FastAPI(title="Boter 2025 API")

# CORS Middleware config | إعدادات CORS
# Allows requests from the React Frontend (usually running on port 3000/5173).
# يسمح بالطلبات من الواجهة الأمامية.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import datetime
    print(f"[{datetime.datetime.now()}] Incoming: {request.method} {request.url}")
    try:
        response = await call_next(request)
        print(f"[{datetime.datetime.now()}] Response: {response.status_code}")
        return response
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Failed: {e}")
        raise e
@app.on_event("startup")
async def startup():
    """
    Run on application startup.
    🔹 يعمل عند تشغيل التطبيق.
    """
    # Connect to MongoDB if configured
    # الاتصال بـ MongoDB إذا كانت الإعدادات موجودة
    from backend.services.mongo_service import connect_mongo
    await connect_mongo()

# Include Routers | تضمين الموجهات
app.include_router(setup.router)

from backend.routers import dashboard
app.include_router(dashboard.router)

@app.get("/")
async def root():
    """
    Root endpoint to check status.
    🔹 نقطة الجذر للتحقق من الحالة.
    """
    config = get_system_config()
    if not config.is_setup_complete:
        return {"message": "مرحباً في بوتر 2025. يرجى إكمال الإعداد أولاً عبر /setup"}
    return {"message": "نظام بوتر 2025 يعمل بنجاح."}
