# ⚡ أوامر سريعة للنشر

## النشر الأول

```bash
# 1. استنساخ
git clone https://github.com/YOUR_USERNAME/vex-bot.git
cd vex-bot

# 2. الإعدادات
cp .env.production.example .env.production
nano .env.production  # عدّل البيانات

# 3. التشغيل
docker-compose -f docker-compose.production.yml up -d

# 4. المراقبة
docker-compose -f docker-compose.production.yml logs -f vex-bot
```

---

## الأوامر اليومية

```bash
# شاهد الحالة
docker-compose -f docker-compose.production.yml ps

# شاهد السجلات
docker-compose -f docker-compose.production.yml logs -f vex-bot

# أعد التشغيل
docker-compose -f docker-compose.production.yml restart vex-bot

# أوقف البوت
docker-compose -f docker-compose.production.yml down

# احذف البيانات القديمة
docker-compose -f docker-compose.production.yml down -v
```

---

## التحديثات

```bash
# اسحب التحديثات من GitHub
git pull origin main

# أعد البناء والتشغيل
docker-compose -f docker-compose.production.yml up -d --build

# شاهد السجلات
docker-compose -f docker-compose.production.yml logs -f vex-bot
```

---

## البحث عن الأخطاء

```bash
# السجلات الكاملة
docker-compose -f docker-compose.production.yml logs vex-bot

# آخر 100 سطر
docker-compose -f docker-compose.production.yml logs --tail=100 vex-bot

# استهلاك الموارد
docker stats vex_bot

# ادخل الحاوية
docker exec -it vex_bot bash
```

---

## Portainer

```bash
# تثبيت Portainer
docker run -d -p 8000:8000 -p 9000:9000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  --name portainer --restart always \
  portainer/portainer-ce

# الدخول: http://your-ip:9000
```

**تم!** 🚀
