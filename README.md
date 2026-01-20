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
- MongoDB Connection String (Atlas or External)

### Steps / الخطوات

1. **Clone the repository / استنسخ المستودع**
   ```bash
   git clone https://github.com/twuijri/Vex.git
   cd Vex
   ```

2. **Setup (لوحة الإعداد)**
   شغّل النظام ثم افتح المتصفح على `http://localhost:3000` لإدخال:
   - توكن البوت
   - رابط MongoDB
   - **اسم قاعدة البيانات (اختياري، الافتراضي: Vex_db)**
   - بيانات دخول اللوحة

3. **Run with Docker / التشغيل بواسطة دوكر**
   ```bash
   docker-compose up -d --build
   ```

4. **Access Dashboard / الدخول للوحة التحكم**
   Open your browser:
   افتح المتصفح:
   `http://localhost:3000`

    `http://localhost:3000`

### ⚡ Quick Start (One Command)
Run the entire system with a single command (Linux/Mac):
تشغيل النظام بالكامل بأمر واحد:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/twuijri/Vex/main/docker-compose.ghcr.yml && docker compose up -d
```
*Note: After running, open `http://localhost:3000` to configure the Bot Token & Admin User via the Setup Wizard.*
*ملاحظة: بعد التشغيل، افتح الرابط `http://localhost:3000` لإدخال التوكن وإعداد المشرف عبر المعالج التلقائي.*

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
