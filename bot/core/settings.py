"""قراءة الإعدادات من config.json فقط"""
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "config.json"

class Settings:
    def __init__(self):
        self.BOT_TOKEN = ""
        self.MONGO_URI = ""
        self.MONGO_DB_NAME = "Vex_db"
        self.load()
    
    def load(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.BOT_TOKEN = data.get('BOT_TOKEN', '')
                self.MONGO_URI = data.get('MONGO_URI', '')
                self.MONGO_DB_NAME = data.get('MONGO_DB_NAME', 'Vex_db')

settings = Settings()
