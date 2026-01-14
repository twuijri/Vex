# استخدام Python 3.11 كصورة أساسية
FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# إنشاء مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود البوت
COPY . .

# إنشاء مستخدم غير root للأمان
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# التبديل للمستخدم الجديد
USER botuser

# نقطة الدخول: اختبر الإعدادات أولاً
ENTRYPOINT ["python", "/app/startup.py"]
