# 🐳 تعليمات نشر البوت على Portainer

## المتطلبات
- سيرفر مع Docker مثبت
- Portainer مثبت وتشغيل
- MongoDB Atlas (قاعدة بيانات سحابية)

## خطوات النشر

### 1️⃣ الإعدادات الأساسية

#### قاعدة البيانات MongoDB
1. اذهب إلى [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. أنشئ حساب أو سجل الدخول
3. أنشئ Cluster جديد
4. احصل على Connection String:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/?appName=yourapp
   ```

#### بوت Telegram
1. تحدث مع [@BotFather](https://t.me/botfather)
2. أنشئ بوت جديد بأمر `/newbot`
3. انسخ ال Token

### 2️⃣ نشر على Portainer

#### أ) الخطوة الأولى: فتح Portainer
```
http://your-server-ip:9000
```

#### ب) إنشاء Stack جديد
1. انقر على **Stacks** من الجانب الأيسر
2. اضغط **Add Stack**
3. أدخل الاسم: `coffeebot`
4. في قسم **Web editor**، انسخ محتوى `docker-compose.prod.yml`

#### ج) إضافة Variables
بعد نسخ الـ compose، اضغط **Advanced mode** وأضف:

```yaml
version: '3.8'

services:
  bot:
    image: abdulaziz/coffeebot:latest
    container_name: telegram_bot
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
      - ./logs:/app/logs
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

#### د) تعيين القيم
في قسم **Environment variables** أسفل الشاشة، أضف:

| المتغير | القيمة | مثال |
|---------|--------|------|
| `BOT_TOKEN` | توكن البوت من BotFather | `432166173:AAEVpOpUPyQ4lrpnrFyuu...` |
| `MONGO_URI` | رابط MongoDB Atlas | `mongodb+srv://user:pass@cluster.mongodb.net/?appName=coffeeBot` |
| `MONGO_DB_NAME` | اسم قاعدة البيانات | `coffeeBot` |
| `ADMIN_IDS` | معرف أو معرفات الأدمن | `123456789` أو `123456789,987654321` |
| `ADMIN_GROUP_ID` | معرف مجموعة الأدمن (سالب) | `-1001234567890` |

### 3️⃣ النشر والتشغيل

1. انقر **Deploy Stack**
2. انتظر حتى يصبح الحالة **Running** (أخضر)
3. اختبر البوت في Telegram: `/start`

### 4️⃣ مراقبة السجلات

1. انقر على اسم الـ Stack
2. انقر على **Logs**
3. ستشوف:
   ```
   ✅ Connected to MongoDB: coffeeBot
   ✅ Bot started
   ```

---

## 🔄 التحديثات

عندما تحدث تغييرات في الكود:

### الطريقة 1: Push إلى Registry ثم Re-pull
```bash
docker build -t abdulaziz/coffeebot:latest .
docker push abdulaziz/coffeebot:latest

# في Portainer:
# Stack > coffeebot > Remove > Create جديد
```

### الطريقة 2: Upload الملفات مباشرة
1. في Portainer اختر **Volumes**
2. Copy الملفات الجديدة
3. Restart Container

---

## ⚠️ استكشاف الأخطاء

### البوت لا يتصل بـ MongoDB
```
❌ Failed to connect to MongoDB
```
**الحل:** تحقق من:
- `MONGO_URI` صحيح
- المستخدم والباسوورد صحيح
- الـ IP whitelist في MongoDB Atlas يسمح بالوصول

### البوت يتوقف فوراً
**تحقق من:**
- `BOT_TOKEN` صحيح
- `MONGO_DB_NAME` موجود فعلاً في MongoDB

### التصريحات غير كاملة
- تأكد أن البوت مشرف في المجموعة
- أعطه: حذف الرسائل، حظر، دعوة

---

## 💡 نصائح مهمة

1. **Backup قاعدة البيانات دورياً** من MongoDB Atlas
2. **استخدم Secrets في Portainer** بدلاً من كتابة الباسوورد مباشرة (أمان)
3. **راقب السجلات** بانتظام عشان تكتشف المشاكل مبكراً
4. **استخدم DNS** بدلاً من IP مباشر للسيرفر

---

## 📞 الدعم

إذا واجهت مشكلة:
1. تحقق من السجلات (Logs)
2. تأكد من جميع المتغيرات
3. اتصل بفريق الدعم أو فتح Issue

---

النسخة: **2025.01.14**
آخر تحديث: **14 يناير 2025**
