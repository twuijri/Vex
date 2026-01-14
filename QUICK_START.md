# ⚡ البدء السريع - CoffeeBot on Portainer

**5 دقائق فقط لتشغيل البوت على السيرفر**

---

## الخطوة الأولى: جمع البيانات (3 دقائق)

### 1. توكن البوت
```
تحدث مع @BotFather في Telegram:
/newbot
اسم البوت + اسم مستخدم
احفظ الـ TOKEN
```

### 2. قاعدة البيانات MongoDB
```
اذهب إلى: https://www.mongodb.com/cloud/atlas
أنشئ cluster مجاني
اسم: coffeeBot
احصل على Connection String:
mongodb+srv://user:password@cluster.mongodb.net/?appName=coffeeBot
```

### 3. معرفك الشخصي
```
تحدث مع @userinfobot
احفظ رقمك (مثل: 123456789)
```

### 4. مجموعة الإدارة
```
أنشئ مجموعة جديدة "Admin Group"
أضف البوت مشرفاً
ارسل /start للبوت
البوت سيخبرك برقمها (مثل: -1001234567890)
```

---

## الخطوة الثانية: النشر (2 دقائق)

### في Portainer:

1. **Stacks** → **Add Stack**

2. اسم: `coffeebot`

3. نسخ هذا:
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
      - LOG_LEVEL=INFO
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

4. **Environment Variables** (أسفل الشاشة):
```
BOT_TOKEN = 432166173:AAEVpOpUPyQ4...
MONGO_URI = mongodb+srv://user:pass@cluster...
MONGO_DB_NAME = coffeeBot
ADMIN_IDS = 123456789
ADMIN_GROUP_ID = -1001234567890
```

5. **Deploy Stack** ✅

---

## التحقق من النجاح

### في Portainer:
```
Stacks > coffeebot > Logs

ابحث عن:
✅ Connected to MongoDB: coffeeBot
✅ Bot started: @your_bot_name
```

### في Telegram:
```
/start في البوت
إذا رد عليك = نجح! ✅
```

---

## المشاكل الشائعة

### ❌ "Failed to connect to MongoDB"
**الحل:** 
- تأكد من username و password صحيح
- أضف IP الخادم في MongoDB Atlas > Network Access

### ❌ "Unauthorized"
**الحل:** 
- تحقق من BOT_TOKEN عند @BotFather

### ❌ "No groups found" في الأعدادات
**الحل:**
- تأكد من MONGO_DB_NAME صحيح
- البيانات القديمة موجودة في coffeeBot

---

## الخطوة التالية

انقر `/admin` في البوت لفتح لوحة التحكم 🎮

---

**المدة الكلية:** ~5 دقائق  
**المستوى:** مبتدئ  
**الدعم:** اقرأ DEPLOYMENT.md للتفاصيل
