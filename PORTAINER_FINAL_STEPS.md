# ✅ خطوات النشر النهائية في Portainer

## 📌 الخطوات (محدّثة):

### 1️⃣ في Portainer: Stacks → Add stack

### 2️⃣ اختر Repository

**Stack name:** `vex-bot`

**Build method:** اختر **Repository**

### 3️⃣ معلومات Git Repository

```
Repository URL: https://github.com/twuijri/Vex.git

Repository reference: refs/heads/main

Compose path: portainer-stack.yml
```

### 4️⃣ ⚠️ **لا تضيف Environment Variables الآن!**

**MongoDB URI سيتم ضبطه من لوحة التحكم بعد التشغيل**، لذلك اترك قسم Environment variables فارغاً.

### 5️⃣ Deploy the stack

اضغط **Deploy the stack** وانتظر حتى يتم بناء ونشر الـ Containers.

---

## 🎯 بعد النشر:

### 1. افتح التطبيق:
```
http://your-server-ip:8000
```

### 2. أكمل الإعداد الأولي:
- أدخل بيانات الأدمن (username, password)
- أدخل **MongoDB URI** في لوحة التحكم
- أدخل **Bot Token** من @BotFather
- أدخل **Support Group ID** و **Log Channel ID**

### 3. احفظ الإعدادات

الإعدادات ستُحفظ في ملف `config.db` داخل مجلد `data/` (persistent volume).

---

## 📊 الـ Containers المتوقعة:

بعد النشر، يجب أن ترى:
- ✅ `boter_backend` (Port 8000)
- ✅ `boter_bot`
- ✅ `boter_frontend` (Port 3000)

---

## 🔍 الوصول للتطبيق:

- **Backend & Setup:** `http://your-server-ip:8000`
- **Frontend Dashboard:** `http://your-server-ip:3000`

---

## 🛠️ ملاحظات مهمة:

1. **المجلد `/data/` مهم جداً!**
   - يحتوي على `config.db` (إعدادات النظام)
   - يجب أن يكون persistent volume

2. **إذا لم يعمل البناء (Build) في Portainer:**
   - سجل دخول SSH للسيرفر
   - نفذ:
   ```bash
   cd /root
   git clone https://github.com/twuijri/Vex.git
   cd Vex
   docker build -f docker/Dockerfile.backend -t vex-backend:latest .
   docker build -f docker/Dockerfile.bot -t vex-bot:latest .
   ```
   - ثم عدّل Stack لاستخدام `image` بدلاً من `build`

3. **Firewall:**
   تأكد من فتح Ports:
   ```bash
   firewall-cmd --permanent --add-port=8000/tcp
   firewall-cmd --permanent --add-port=3000/tcp
   firewall-cmd --reload
   ```

---

## 🔄 تحديث المشروع مستقبلاً:

```bash
# في جهازك المحلي
git add .
git commit -m "Update description"
git push origin main
```

**في Portainer:**
- اذهب للـ Stack `vex-bot`
- اضغط **Update the stack**
- اختر **Pull and redeploy**

---

**الآن جاهز للنشر! 🚀**

لا تنسى ضبط MongoDB من لوحة التحكم بعد التشغيل!
