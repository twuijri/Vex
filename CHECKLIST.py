#!/usr/bin/env python3
"""
Pre-deployment checklist for CoffeeBot
قائمة التحقق قبل النشر
"""

checks = {
    "📋 متغيرات البيئة": {
        ".env": [
            "BOT_TOKEN موجود وليس فارغ",
            "MONGO_URI موجود مع رابط كامل",
            "MONGO_DB_NAME موجود",
            "ADMIN_IDS موجود",
            "LOG_LEVEL موجود",
        ],
        ".env.example": [
            "يحتوي على قالب المتغيرات",
            "يحتوي على شرح عربي",
        ],
    },
    "🔧 ملفات التكوين": {
        "bot/core/config.py": [
            "يقرأ MONGO_DB_NAME من ENV",
            "له default value",
        ],
        "bot/database/connection.py": [
            "يستخدم config.MONGO_DB_NAME",
            "لا يستخرج من MONGO_URI",
        ],
    },
    "🐳 Docker": {
        "Dockerfile": [
            "موجود وصحيح",
        ],
        "docker-compose.yml": [
            "بدون MongoDB محلي (سحابي فقط)",
            "يقرأ متغيرات من .env",
        ],
        "docker-compose.prod.yml": [
            "موجود وجاهز للإنتاج",
            "يستخدم صورة جاهزة",
        ],
        "docker-stack.yml": [
            "موجود لـ Portainer",
            "فيه شروحات كاملة",
        ],
    },
    "📚 التوثيق": {
        "DEPLOYMENT.md": [
            "شرح النشر خطوة بخطوة",
            "قائمة المتغيرات مع الأمثلة",
        ],
        "PORTAINER_GUIDE.md": [
            "شرح مفصل لـ Portainer",
            "خطوات النشر والتحديثات",
        ],
        "CHANGES_SUMMARY.md": [
            "ملخص التغييرات",
            "قائمة الملفات الجديدة",
        ],
    },
    "🛠️ أدوات التطوير": {
        "dev.sh": [
            "executable",
            "يحتوي على أوامر التطوير",
        ],
        "health_check.py": [
            "executable",
            "يختبر الإعدادات والاتصال",
        ],
    },
    "🔐 الأمان": {
        ".gitignore": [
            ".env.production موجود فيه",
            ".env.local موجود فيه",
        ],
    },
}

if __name__ == "__main__":
    print("=" * 60)
    print("CoffeeBot Pre-Deployment Checklist")
    print("قائمة التحقق قبل النشر")
    print("=" * 60)
    
    total = 0
    for category, items in checks.items():
        print(f"\n{category}")
        for file_or_section, requirements in items.items():
            print(f"  📄 {file_or_section}")
            for req in requirements:
                print(f"     □ {req}")
                total += 1
    
    print("\n" + "=" * 60)
    print(f"إجمالي المتطلبات: {total}")
    print("=" * 60)
    print("\nنصائح:")
    print("1. تأكد من وجود جميع الملفات")
    print("2. اختبر locally قبل الإرسال")
    print("3. تحقق من السجلات (logs) على Portainer")
    print("4. استخدم health_check.py للتحقق السريع")
    print("=" * 60)
