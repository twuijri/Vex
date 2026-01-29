# 🔧 حل مشاكل Frontend في Portainer

## المشكلة: `boter_frontend` exited (code 254)

الـ Frontend Container يطفي بعد التشغيل مباشرة.

---

## ✅ الحل:

### 1️⃣ Update Stack في Portainer:

تم تحديث `docker-compose.yml` على GitHub بالتحسينات التالية:
- ✅ إضافة `restart: always` للـ frontend
- ✅ تحسين npm install command
- ✅ إضافة `--verbose` لرؤية تفاصيل التثبيت
- ✅ `--host 0.0.0.0` للـ Vite dev server

**في Portainer:**
1. اذهب إلى Stack `vex`
2. اضغط **Pull and redeploy** (أو Update the stack)
3. انتظر حتى يعيد البناء

---

### 2️⃣ شوف Logs:

أثناء التحديث، شوف Logs للـ Frontend:
1. **Containers** → `boter_frontend`
2. **Logs**
3. شوف تقدم `npm install`

---

### 3️⃣ إذا استمرت المشكلة:

#### الحل البديل: بناء Frontend كـ Image منفصل

إذا npm install يفشل باستمرار، يمكنك بناء Frontend image جاهز:

**على السيرفر عبر SSH:**
```bash
cd /root/Vex
docker build -f docker/Dockerfile.frontend -t vex-frontend:latest .
```

**ثم عدّل docker-compose.yml:**
```yaml
frontend:
  image: vex-frontend:latest
  # حذف command: npm install...
```

---

## 🔍 الأسباب الشائعة:

1. **npm install بطيء جداً** → الحل: Frontend Dockerfile مع pre-built image
2. **مشكلة في node_modules** → الحل: حذف volume للـ frontend
3. **Vite dev server ما يشتغل** → الحل: التأكد من `--host 0.0.0.0`

---

## 📊 التحقق من النجاح:

بعد Update:
```
boter_backend   → running ✅
boter_bot       → running ✅
boter_frontend  → running ✅ (ما يكون exited)
```

افتح:
```
http://your-server-ip:8000  → Backend API
http://your-server-ip:3000  → Frontend Dashboard
```

---

## 🆘 إذا ما زال Frontend يطفي:

**أرسل Logs للـ Frontend:**

في Portainer → boter_frontend → Logs → انسخ آخر 50 سطر

سأساعدك في تحليل المشكلة.
