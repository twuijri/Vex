# 🚀 دليل النشر على السيرفر

## المتطلبات

- سيرفر بـ Docker و Docker Compose
- MongoDB Atlas (قاعدة بيانات سحابية)
- توكن البوت من @BotFather

## خطوات النشر على السيرفر

### 1️⃣ استنساخ المشروع

```bash
git clone https://github.com/YOUR_USERNAME/vex-bot.git
cd vex-bot
```

### 2️⃣ إنشاء ملف البيانات

```bash
cp .env.production.example .env.production
```

ثم عدّل `.env.production` بـ `nano` أو `vim`:

```bash
nano .env.production
```

أدخل بيانات:
```
BOT_TOKEN=YOUR_TOKEN_HERE
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/?appName=yourapp
ADMIN_GROUP_ID=-1001234567890
SUPER_ADMINS=123456789
```

اضغط: `Ctrl+X` ثم `Y` ثم `Enter` للحفظ

### 3️⃣ بناء وتشغيل البوت

```bash
docker-compose -f docker-compose.production.yml up -d
```

### 4️⃣ التحقق من الحالة

```bash
# شاهد السجلات
docker-compose -f docker-compose.production.yml logs -f vex-bot

# تحقق من حالة الحاوية
docker-compose -f docker-compose.production.yml ps
```

### 5️⃣ إيقاف البوت

```bash
docker-compose -f docker-compose.production.yml down
```

### 6️⃣ إعادة تشغيل البوت

```bash
docker-compose -f docker-compose.production.yml restart vex-bot
```

---

## 🐳 أوامر Docker مفيدة

```bash
# شاهد السجلات الآخيرة 50 سطر
docker-compose -f docker-compose.production.yml logs -n 50 vex-bot

# شاهد السجلات مباشرة (live)
docker-compose -f docker-compose.production.yml logs -f vex-bot

# ادخل الحاوية
docker exec -it vex_bot bash

# تحقق من استهلاك الموارد
docker stats vex_bot
```

---

## 📊 استخدام Portainer (الأسهل)

### 1️⃣ تثبيت Portainer

```bash
docker run -d -p 8000:8000 -p 9000:9000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  --name portainer \
  --restart always \
  portainer/portainer-ce
```

### 2️⃣ افتح Portainer

```
http://your-server-ip:9000
```

### 3️⃣ أنشئ Stack جديد

- Stacks > Add Stack
- اسم: `vex-bot`
- Copy/Paste محتوى `docker-compose.production.yml`
- أضف متغيرات البيئة
- Deploy

---

## 🔄 التحديثات

عندما تحدث تغييرات:

```bash
# اسحب التحديثات
git pull origin main

# أعد بناء الصورة
docker-compose -f docker-compose.production.yml build --no-cache

# أعد تشغيل
docker-compose -f docker-compose.production.yml up -d
```

---

## ⚠️ استكشاف الأخطاء

### البوت لا يبدأ

```bash
# شاهد السجلات
docker-compose -f docker-compose.production.yml logs vex-bot

# تحقق من البيانات في .env.production
cat .env.production
```

### لا يمكن الاتصال بـ MongoDB

```bash
# تأكد من:
1. MONGO_URI صحيح
2. IP الخادم في MongoDB Atlas Network Access
3. بيانات المستخدم صحيحة
```

### استهلاك عالي للموارد

```bash
docker stats vex_bot
```

---

## 💾 Backup

```bash
# احفظ البيانات
docker cp vex_bot:/app/config ./backup_config
docker cp vex_bot:/app/logs ./backup_logs

# أعد الاستعادة
docker cp ./backup_config/. vex_bot:/app/config
```

---

**النسخة:** 2025.01  
**آخر تحديث:** 14 يناير 2025
