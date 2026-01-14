# 🚀 دليل النشر الكامل - CoffeeBot 2025

**الحالة:** مستعد للإنتاج ✅  
**النسخة:** 2025.01.14  
**التاريخ:** 14 يناير 2025

---

## 📊 ملخص سريع

| الميزة | التفاصيل |
|--------|---------|
| **البيانات** | MongoDB Cloud (coffeeBot) |
| **الكود** | aiogram 3.x + Beanie ODM |
| **النشر** | Docker + Portainer |
| **المتغيرات** | 6 متغيرات أساسية فقط |
| **الحالة** | جاهز للإنتاج |

---

## 🔧 المتغيرات المطلوبة (6 فقط)

### 1. `BOT_TOKEN` ⭐
**من:** @BotFather في Telegram  
**صيغة:** `123456789:ABCDefGhIjKlMnOpQrStUvWxYz...`

### 2. `MONGO_URI` 🗄️
**من:** MongoDB Atlas > Connect > Connection String  
**صيغة:** `mongodb+srv://username:password@cluster.mongodb.net/?appName=app`

### 3. `MONGO_DB_NAME` 🔑
**القيمة:** اسم قاعدة البيانات  
**مثال:** `coffeeBot`

### 4. `ADMIN_IDS` 👨‍💼
**صيغة:** `123456789` أو `123456789,987654321`  
**مثال:** `218369077`

### 5. `ADMIN_GROUP_ID` 👥
**صيغة:** سالبة: `-1001234567890`

### 6. `LOG_LEVEL` (اختياري)
**الخيارات:** `DEBUG`, `INFO`, `WARNING`, `ERROR`  
**الافتراضي:** `INFO`

---

## 🐳 النشر على Portainer

### الخطوة 1: فتح Portainer
```
http://your-server-ip:9000
```

### الخطوة 2: إنشاء Stack جديد
1. **Stacks** > **Add Stack**
2. الاسم: `coffeebot`

### الخطوة 3: نسخ docker-compose
```yaml
version: '3.8'

services:
  bot:
    image: abdulaziz/coffeebot:latest
    container_name: coffeebot_telegram
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - MONGO_URI=${MONGO_URI}
      - MONGO_DB_NAME=${MONGO_DB_NAME}
      - ADMIN_IDS=${ADMIN_IDS}
      - ADMIN_GROUP_ID=${ADMIN_GROUP_ID}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - TZ=Asia/Riyadh
    volumes:
      - ./logs:/app/logs:rw
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - bot_network

networks:
  bot_network:
    driver: bridge
```

### الخطوة 4: إضافة Environment Variables
أسفل الشاشة، أضف المتغيرات الـ 6:

| المتغير | القيمة |
|---------|--------|
| `BOT_TOKEN` | توكنك من @BotFather |
| `MONGO_URI` | رابط MongoDB Atlas |
| `MONGO_DB_NAME` | `coffeeBot` |
| `ADMIN_IDS` | `218369077` |
| `ADMIN_GROUP_ID` | `-1001234567890` |
| `LOG_LEVEL` | `INFO` |

### الخطوة 5: النشر
اضغط **Deploy Stack** ✅

### الخطوة 6: التحقق من الحالة
**Logs** يجب يظهر:
```
✅ Connected to MongoDB: coffeeBot
✅ Bot started: @your_bot_username
```

---

## 🔄 التحديثات

```bash
# بعد تعديل الكود وpush للـ repo:

# في Portainer:
# Stacks > coffeebot > Remove
# ثم أنشئ stack جديدة بنفس الخطوات
```

---

## ⚠️ استكشاف الأخطاء

### ❌ قاعدة البيانات خاطئة
```
Connected to MongoDB: boter_db (خطأ!)
```
**الحل:** تأكد من `MONGO_DB_NAME=coffeeBot`

### ❌ اتصال MongoDB فاشل
```
❌ Failed to connect to MongoDB
```
**الحل:** تحقق من:
- `MONGO_URI` صحيح
- Username و Password صحيحين
- IP whitelist في MongoDB Atlas

### ❌ البوت لا يرد
```
❌ Unauthorized
```
**الحل:** `BOT_TOKEN` خاطئ - تحقق من @BotFather

---

## ✅ قائمة التحقق

- [ ] MongoDB Atlas cluster + مستخدم
- [ ] توكن من @BotFather
- [ ] مجموعة إدارة مع معرّفها
- [ ] معرّف الأدمن
- [ ] كل 6 متغيرات في Portainer
- [ ] Stack deployed بنجاح
- [ ] البوت يرد على `/start`

---

**الحالة:** ✅ جاهز للإنتاج  
**آخر تحديث:** 2025-01-14
