from datetime import datetime, timedelta
from typing import Optional
import os
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer
from backend.database.local_db import get_system_config
import bcrypt

# ==============================================================================
# 📄 File: backend/auth.py
# 📝 Description: Authentication logic (JWT & Hashing).
# 📝 الوصف: منطق المصادقة (JWT والتشفير).
# ==============================================================================

# Secret Key Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 Days

# Endpoint where frontend requests token | نقطة طلب التوكن
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def verify_password(plain_password, hashed_password):
    """
    Verify password against hash.
    🔹 التحقق من صحة كلمة المرور مقابل التشفير.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    """
    Generate password hash.
    🔹 توليد تشفير لكلمة المرور.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a new JWT Access Token.
    🔹 إنشاء توكن دخول جديد.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    # Using a hardcoded secret for now. Ideally, this should be generated or from ENV.
    # نستخدم مفتاح ثابت حالياً للتسهيل، يفضل توليده أو جلبه من المتغيرات البيئية.
    encoded_jwt = jwt.encode(to_encode, "SUPER_SECRET_KEY_CHANGE_ME", algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current authenticated admin user.
    🔹 دالة (Dependency) للحصول على المدير الحالي المصادق عليه.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, "SUPER_SECRET_KEY_CHANGE_ME", algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Verify against stored config | التحقق من البيانات المخزنة
    config = get_system_config()
    if username != config.admin_username:
        raise credentials_exception
    return username
