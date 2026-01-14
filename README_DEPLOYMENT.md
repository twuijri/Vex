# 🤖 Vex Bot - دليل النشر السريع

## 📋 المتطلبات

✅ سيرفر بـ Docker و Docker Compose  
✅ MongoDB Atlas (مجاني)  
✅ توكن البوت من @BotFather  

---

## 🚀 النشر في 4 خطوات

### الخطوة 1: استنساخ المشروع

```bash
git clone https://github.com/YOUR_USERNAME/vex-bot.git
cd vex-bot
```

### الخطوة 2: إعداد البيانات

```bash
cp .env.production.example .env.production
nano .env.production
```

أضف:
```env
BOT_TOKEN=YOUR_TOKEN
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/?appName=yourapp
ADMIN_GROUP_ID=-1001234567890
SUPER_ADMINS=123456789
```

### الخطوة 3: التشغيل

```bash
docker-compose -f docker-compose.production.yml up -d
```

### الخطوة 4: المراقبة

```bash
docker-compose -f docker-compose.production.yml logs -f vex-bot
```

✅ البوت يعمل الآن!

---

## 📚 التوثيق الكاملة

- **DEPLOYMENT_GUIDE.md** - شرح مفصل
- **QUICK_COMMANDS.md** - أوامر سريعة
- **QUICK_START.md** - للاستخدام المحلي

---

## 🔄 Portainer (الأسهل)

```bash
# تثبيت
docker run -d -p 8000:8000 -p 9000:9000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  --name portainer --restart always \
  portainer/portainer-ce

# الدخول: http://your-server:9000
```

ثم:
1. Stacks > Add Stack
2. Copy/Paste من `docker-compose.production.yml`
3. أضف متغيرات البيئة
4. Deploy ✅

---

## 💡 نصائح

```bash
# شاهد السجلات
docker-compose -f docker-compose.production.yml logs -f vex-bot

# أعد التشغيل
docker-compose -f docker-compose.production.yml restart vex-bot

# التحديثات
git pull && docker-compose -f docker-compose.production.yml up -d --build
```

---

**جاهز للنشر!** 🎉
