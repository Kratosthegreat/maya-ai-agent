import sys
print(f"📦 רץ על גרסת פייתון: {sys.version}")

import logging
import random
import asyncio
import httpx
import os
import json
from datetime import datetime, time
import pytz
from telegram import Update, Bot
from telegram.ext import (
    Application, ContextTypes, MessageHandler, CommandHandler,
    filters
)
import google.generativeai as genai
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# === טוקנים מהסביבה ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise EnvironmentError("חסר TELEGRAM_TOKEN או GEMINI_API_KEY")

# === קונפיגורציית Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
print("✅ Gemini API מחובר בהצלחה")

# === קובץ זיכרון ===
MEMORY_FILE = "maya_memory.json"
user_memory = {}
chat_sessions = {}

def load_memory():
    global user_memory
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            user_memory = json.load(f)
            print(f"✅ נטען זיכרון עבור {len(user_memory)} משתמשים")

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(user_memory, f, ensure_ascii=False, indent=2)

def update_user_memory(user_id, new_info):
    user_id = str(user_id)
    if user_id not in user_memory:
        user_memory[user_id] = {}
    user_memory[user_id].update(new_info)
    save_memory()

def get_user_context(user_id):
    return json.dumps(user_memory.get(str(user_id), {}), ensure_ascii=False)

def get_current_time_israel():
    now = datetime.now(pytz.timezone("Asia/Jerusalem"))
    return now.strftime('%H:%M:%S'), now.strftime('%A, %d %B %Y')

def create_enhanced_system_prompt(user_id):
    current_time, current_date = get_current_time_israel()
    return f"""
את מאיה - בוט טלגרם חמוד ועוזר! 🤖
📅 תאריך: {current_date}
🕐 שעה: {current_time}
📍 מיקום: ישראל

מידע על המשתמש:
{get_user_context(user_id)}

האישיות שלך:
- חמה, חכמה וחייכנית
- עונה בעברית טבעית
- זוכרת מידע חשוב
- משתמשת באמוג׳ים עדין
- מגיבה באמפתיה, הומור או חום לפי הקשר
"""

def create_chat_session(user_id):
    try:
        chat = model.start_chat(history=[])
        system_prompt = create_enhanced_system_prompt(user_id)
        chat.send_message(system_prompt)
        return chat
    except Exception as e:
        logging.error(f"שגיאה בצ'אט עם Gemini: {e}")
        return None

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text.strip()

    if user_id not in chat_sessions:
        chat_sessions[user_id] = create_chat_session(user_id)
        if not chat_sessions[user_id]:
            await update.message.reply_text("😅 תקלה זמנית, נסה שוב עוד רגע.")
            return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = chat_sessions[user_id].send_message(msg)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"שגיאה ב-Gemini: {e}")
        chat_sessions[user_id] = create_chat_session(user_id)
        await update.message.reply_text("😅 משהו השתבש, אפשר לנסות שוב?")

# === פקודות ===
async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = user_memory.get(user_id)
    if not data:
        await update.message.reply_text("🤔 לא זוכרת כלום עדיין! ספר לי משהו עליך.")
    else:
        text = "\n".join([f"• {k}: {v}" for k, v in data.items()])
        await update.message.reply_text("🧠 מה שאני זוכרת:\n" + text)

async def forget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in user_memory:
        del user_memory[user_id]
        save_memory()
        await update.message.reply_text("🧹 מחקתי הכל! בוא נתחיל מחדש.")
    else:
        await update.message.reply_text("לא שמרתי עליך כלום עדיין 😊")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = len(user_memory)
    chats = len(chat_sessions)
    now, date = get_current_time_israel()
    await update.message.reply_text(
        f"📊 סטטיסטיקות מאיה:\n👥 משתמשים: {users}\n💬 צ׳אטים פעילים: {chats}\n🕐 שעה: {now}\n📅 תאריך: {date}"
    )

# === הודעות יזומות ===
async def morning_message(context: ContextTypes.DEFAULT_TYPE):
    for uid in user_memory:
        try:
            name = user_memory[uid].get("name", "חבר")
            await context.bot.send_message(chat_id=int(uid), text=f"☀️ בוקר טוב {name}! אני פה אם תצטרך אותי היום 💚")
        except Exception as e:
            logging.error(f"שליחת בוקר ל-{uid} נכשלה: {e}")

async def reminder_message(context: ContextTypes.DEFAULT_TYPE):
    texts = [
        "רק מזכירה – לשתות מים 💧",
        "נשימה עמוקה? מגיע לך רגע שקט 🧘‍♀️",
        "מה עם משהו נחמד רק בשבילך היום? 💛",
    ]
    for uid in user_memory:
        try:
            await context.bot.send_message(chat_id=int(uid), text=random.choice(texts))
        except Exception as e:
            logging.error(f"שגיאה בתזכורת ל-{uid}: {e}")

# === שרת בריאות ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Maya Bot is running!")

def start_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"✅ שרת בריאות על פורט {port}")
    server.serve_forever()

# === MAIN ===
async def main():
    load_memory()

    print("🚀 מתחילה להפעיל את מאיה...")

    # נקה webhook קודם
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook נוקה")
    except Exception as e:
        print(f"⚠️ שגיאה בניקוי webhook: {e}")

    # בריאות ב-thread
    threading.Thread(target=start_health_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # פקודות
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("forget", forget_command))
    app.add_handler(CommandHandler("stats", stats_command))

    # תזמון
    tz = pytz.timezone("Asia/Jerusalem")
    app.job_queue.run_daily(morning_message, time=time(8, 0, tzinfo=tz))
    app.job_queue.run_daily(reminder_message, time=time(14, 0, tzinfo=tz))

    print("🎉 מאיה מוכנה! שולחת אהבה 🤗")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
