# Vex 🤖
**Advanced Telegram Group Management Bot with Dashboard**
**بوت إدارة مجموعات تيليجرام متطور مع لوحة تحكم**

[![Developer](https://img.shields.io/badge/Developer-@twuijri-blue)](https://github.com/twuijri)
[![Docker](https://img.shields.io/badge/Docker-Ready-green)](https://www.docker.com/)

## 📖 About / نبذة
**Vex** is a powerful, open-source Telegram bot designed to manage groups efficiently. It features a modern web dashboard for easy configuration, real-time statistics, and advanced moderation tools.
**Vex** هو بوت مفتوح المصدر لإدارة مجموعات تيليجرام بكفاءة عالية. يتميز بلوحة تحكم ويب عصرية لسهولة الإعداد، إحصائيات لحظية، وأدوات إشراف متقدمة.

---

## ✨ Features / المميزات
- 🛡️ **Group Protection**: Anti-spam, media filters, and banned words.
- 📊 **Web Dashboard**: Google Material Design UI to manage settings.
- 📈 **Real-time Stats**: Track active groups and messages.
- 🔇 **Silent Mode**: Schedule group opening/closing times.
- 📝 **Welcome Messages**: Customizable welcome texts with variables.
- 🐳 **Dockerized**: Easy deployment with one command.

---

## 🚀 Installation / التثبيت

### Prerequisites / المتطلبات
- Docker & Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- MongoDB (Optional, included in Docker)

### Steps / الخطوات

1. **Clone the repository / استنسخ المستودع**
   ```bash
   git clone https://github.com/twuijri/Vex.git
   cd Vex
   ```

2. **Setup Environment / إعداد المتغيرات**
   Copy the example file and edit it:
   انسخ ملف المثال وقم بتعديله:
   ```bash
   cp .env.example .env
   nano .env
   ```
   *Fill in your `BOT_TOKEN` and Admin credentials.*
   *أدخل توكن البوت وبيانات المشرف.*

3. **Run with Docker / التشغيل بواسطة دوكر**
   ```bash
   docker-compose up -d --build
   ```

4. **Access Dashboard / الدخول للوحة التحكم**
   Open your browser:
   افتح المتصفح:
   `http://localhost:3000`

    `http://localhost:3000`

### 🚀 Option 2: Run using Pre-built Docker Images (Faster) | التشغيل المباشر
Run Vex without building the code manually (No git clone needed for code, just the compose file).
تشغيل البوت بدون الحاجة لبناء الكود يدوياً (أسرع).

1. **Download the Compose File / تحميل ملف التشغيل**
   ```bash
   wget https://raw.githubusercontent.com/twuijri/Vex/main/docker-compose.ghcr.yml -O docker-compose.yml
   ```

2. **Create Configuration / إنشاء الإعدادات**
   Create a `.env` file with your details:
   أنشئ ملف `.env` وضع فيه بياناتك:
   ```bash
   touch .env
   # Add: BOT_TOKEN, ADMIN_PASSWORD, etc.
   ```

3. **Run / تشغيل**
   ```bash
   docker-compose up -d
   ```
   *This will automatically pull the latest images from GitHub Container Registry.*
   *سيقوم هذا الأمر بسحب أحدث النسخ تلقائياً من GitHub.*

---

## 🛠️ Configuration / الإعدادات

### Environment Variables (.env)
| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram Bot Token from BotFather |
| `MONGODB_URI` | Connection string (Default: `mongodb://mongodb:27017/boter_db`) |
| `ADMIN_USERNAME` | Username for Dashboard Login |
| `ADMIN_PASSWORD` | Password for Dashboard Login |

---

## 🤝 Contributing / المساهمة
Contributions are welcome! Please fork the repository and submit a pull request.
نرحب بالمساهمات! يرجى عمل Fork للمستودع وإرسال Pull Request.

## 👤 Developer / المطور
**@twuijri**
[GitHub Profile](https://github.com/twuijri)

---
*Built with Python (Aiogram), React (Vite), and MongoDB.*
*تم بناؤه باستخدام Python و React و MongoDB.*
