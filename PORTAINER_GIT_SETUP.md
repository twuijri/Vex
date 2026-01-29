# خطوات نشر Vex باستخدام Git Repository في Portainer

## ✅ الملفات تم رفعها على GitHub بنجاح!

الآن اتبع هذه الخطوات في **Portainer**:

---

## 📌 الخطوات التفصيلية:

### 1️⃣ افتح Portainer
- اذهب إلى لوحة تحكم Portainer الخاصة بك

### 2️⃣ اذهب إلى Stacks
- من القائمة الجانبية، اختر **Stacks**
- اضغط على **+ Add stack**

### 3️⃣ اختر Repository
- في اسم الـ Stack: `vex-bot` (أو أي اسم تريده)
- اختر تبويب **Repository** (وليس Web editor)

### 4️⃣ أدخل معلومات الـ Repository

**Repository URL:**
```
https://github.com/twuijri/Vex.git
```

**Repository reference:**
```
refs/heads/main
```
(أو اتركه فارغاً لاستخدام main تلقائياً)

**Compose path:**
```
portainer-stack.yml
```

### 5️⃣ إضافة Environment Variables

في قسم **Environment variables**، اضغط **+ add environment variable** وأضف:

| Name | Value |
|------|-------|
| `MONGODB_URI` | `mongodb://your-mongodb-connection-string-here` |

**⚠️ مهم جداً:** استبدل `your-mongodb-connection-string-here` بقيمة الـ MongoDB URI الفعلية!

مثال:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dbname
```

### 6️⃣ Deploy the stack
- اضغط على **Deploy the stack**
- انتظر حتى يتم بناء ونشر الـ Containers

---

## 🔍 التحقق من النشر

بعد النشر، يجب أن ترى 3 containers قيد التشغيل:
- ✅ `boter_backend` (Port 8000)
- ✅ `boter_bot`
- ✅ `boter_frontend` (Port 3000)

---

## 🛠️ ملاحظات مهمة:

### إذا ظهرت مشكلة في البناء (Build)

بعض نسخ Portainer لا تدعم `build` مباشرة من Git repository. في هذه الحالة:

**الحل:**
1. سجل دخول للسيرفر عبر SSH
2. نفذ الأوامر التالية لبناء الـ Images يدوياً:

```bash
# الانتقال للمجلد
cd /root
git clone https://github.com/twuijri/Vex.git
cd Vex

# بناء Backend image
docker build -f docker/Dockerfile.backend -t twuijri/vex-backend:latest .

# بناء Bot image
docker build -f docker/Dockerfile.bot -t twuijri/vex-bot:latest .
```

3. بعدها، عدّل `portainer-stack.yml` واستبدل `build:` بـ `image:`:

```yaml
services:
  backend:
    image: twuijri/vex-backend:latest
    # حذف قسم build

  bot:
    image: twuijri/vex-bot:latest
    # حذف قسم build
```

---

## 🔄 تحديث الـ Stack مستقبلاً

عندما تحدث أي تغيير في الكود:

1. **ارفع التغييرات على GitHub:**
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```

2. **في Portainer:**
   - اذهب إلى Stack `vex-bot`
   - اضغط **Update the stack**
   - اختر **Pull latest image**
   - اضغط **Update**

---

## 📊 الوصول للتطبيق

بعد النشر:
- **Backend API:** `http://your-server-ip:8000`
- **Frontend:** `http://your-server-ip:3000`
- **Bot Dashboard:** عبر الـ Frontend

---

## 🆘 إذا واجهت مشاكل

تحقق من:
1. **Logs** في Portainer لكل Container
2. تأكد من صحة `MONGODB_URI`
3. تأكد من فتح Ports (8000, 3000) في Firewall السيرفر
4. تأكد من وجود ملفات Dockerfile في المسار الصحيح

---

**الآن جاهز للنشر! 🚀**
