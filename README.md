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
