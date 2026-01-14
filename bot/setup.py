"""لوحة الإعداد - مرة واحدة فقط"""
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
import json
from pathlib import Path

app = FastAPI()
CONFIG_DIR = Path(__file__).parent.parent / "data"
CONFIG_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"

HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>إعداد Vex Bot</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { background: white; border-radius: 10px; padding: 40px; max-width: 600px; width: 100%; }
        h1 { color: #333; text-align: center; }
        input, textarea { width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #ddd; border-radius: 5px; font-size: 14px; }
        input:focus, textarea:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 20px; }
        .msg { margin-top: 20px; padding: 15px; border-radius: 5px; display: none; }
        .msg.ok { background: #d4edda; color: #155724; display: block; }
        .msg.err { background: #f8d7da; color: #721c24; display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 إعداد Vex Bot</h1>
        <form id="f">
            <label>توكن البوت 🔑</label>
            <input type="password" name="BOT_TOKEN" required>
            
            <label>رابط MongoDB 🗄️</label>
            <textarea name="MONGO_URI" required></textarea>
            
            <label>اسم قاعدة البيانات 📝</label>
            <input type="text" name="MONGO_DB_NAME" value="Vex_db" required>
            
            <button type="submit">💾 حفظ</button>
            <div class="msg" id="m"></div>
        </form>
    </div>
    <script>
        document.getElementById('f').addEventListener('submit', async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            const d = Object.fromEntries(fd);
            const m = document.getElementById('m');
            try {
                const r = await fetch('/api/setup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(d)
                });
                if (r.ok) {
                    m.className = 'msg ok';
                    m.textContent = '✅ تم الحفظ! البوت سيبدأ...';
                    setTimeout(() => location.reload(), 2000);
                } else {
                    m.className = 'msg err';
                    m.textContent = '❌ خطأ';
                }
            } catch (e) {
                m.className = 'msg err';
                m.textContent = '❌ خطأ: ' + e.message;
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML

@app.post("/api/setup")
async def setup(BOT_TOKEN: str = Form(...), MONGO_URI: str = Form(...), MONGO_DB_NAME: str = Form(...)):
    if not all([BOT_TOKEN.strip(), MONGO_URI.strip(), MONGO_DB_NAME.strip()]):
        raise HTTPException(400, "البيانات ناقصة")
    
    config = {
        "BOT_TOKEN": BOT_TOKEN.strip(),
        "MONGO_URI": MONGO_URI.strip(),
        "MONGO_DB_NAME": MONGO_DB_NAME.strip(),
    }
    
    try:
        CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))
