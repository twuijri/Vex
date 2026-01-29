# تعليمات نشر المشروع في Portainer

## الطريقة 1: استخدام Stack في Portainer (الأسهل)

### الخطوات:

1. **رفع الكود على السيرفر:**
   ```bash
   # على جهازك المحلي
   cd /Users/twuijri/Codeing/Vex
   # رفع المشروع كامل للسيرفر (باستخدام scp أو git)
   ```

2. **في Portainer:**
   - افتح **Portainer** → **Stacks** → **Add stack**
   - اختر اسم للـ Stack مثل: `vex-bot`
   - انسخ محتوى ملف `portainer-stack.yml` في خانة **Web editor**

3. **إضافة المتغيرات البيئية (Environment variables):**
   في Portainer، في قسم **Environment variables**، أضف:
   ```
   MONGODB_URI=mongodb://your-mongodb-uri-here
   ```

4. **اضغط Deploy the stack**

---

## الطريقة 2: رفع المشروع على السيرفر واستخدام Git Repository في Portainer

### الخطوات:

1. **تأكد من رفع الكود على GitHub:**
   ```bash
   cd /Users/twuijri/Codeing/Vex
   git add .
   git commit -m "Update for Portainer deployment"
   git push origin main
   ```

2. **في Portainer:**
   - اذهب إلى **Stacks** → **Add stack**
   - اختر **Repository**
   - أدخل: `https://github.com/twuijri/Vex.git`
   - حدد **Compose path**: `portainer-stack.yml`

3. **أضف Environment variables:**
   ```
   MONGODB_URI=mongodb://your-mongodb-uri-here
   ```

4. **Deploy**

---

## الطريقة 3: بناء Images ثم Deploy (للمشاريع المعقدة)

إذا كان Portainer لا يدعم `build` مباشرة، يمكنك:

1. **بناء الـ Images محلياً أو على السيرفر:**
   ```bash
   # على السيرفر (إذا كان Docker مثبت)
   cd ~/Vex
   
   # بناء Backend image
   docker build -f docker/Dockerfile.backend -t twuijri/vex-backend:latest .
   
   # بناء Bot image
   docker build -f docker/Dockerfile.bot -t twuijri/vex-bot:latest .
   ```

2. **رفع Images إلى Docker Hub (اختياري):**
   ```bash
   docker login
   docker push twuijri/vex-backend:latest
   docker push twuijri/vex-bot:latest
   ```

3. **تعديل `portainer-stack.yml`** واستبدال `build` بـ `image`:
   ```yaml
   backend:
     image: twuijri/vex-backend:latest
     # حذف build:
   
   bot:
     image: twuijri/vex-bot:latest
     # حذف build:
   ```

---

## المشكلة الأساسية: docker-compose غير موجود

إذا أردت تثبيت `docker-compose` على السيرفر (Red Hat/CentOS):

```bash
# طريقة 1: باستخدام Docker Plugin
sudo yum install docker-compose-plugin
# ثم استخدم: docker compose up -d

# طريقة 2: تحميل binary مباشرة
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## الملفات المطلوبة في السيرفر:

عند رفع المشروع للسيرفر، تأكد من وجود:
- `/root/Vex/` (أو المسار الذي تختاره)
- جميع ملفات المشروع (backend, bot, frontend, docker/)
- ملف `.env` أو ضبط Environment variables في Portainer

---

## نصيحة:

الطريقة **الأولى** (Stack في Portainer مباشرة) هي الأسهل والأسرع!
