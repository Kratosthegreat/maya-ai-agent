import os
import requests
from flask import Flask, request, abort

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# משתני סביבה
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Flask app
app = Flask(__name__)

# אתחול הבוט של Telegram
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# === HANDLERS רגילים ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("היי! אני מאיה 🤖 איך אפשר לעזור?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("קיבלתי אותך. 💬 (בקרוב אענה בצורה חכמה יותר)")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Webhook route ל־Telegram ===
@app.route("/webhook", methods=["POST"])
def webhook():
    if WEBHOOK_SECRET_TOKEN:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if token != WEBHOOK_SECRET_TOKEN:
            abort(403)

    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200

# === Route דיאגנוסטיקה: /diagnose ===
@app.route("/diagnose", methods=["GET"])
def diagnose():
    report = []
    def log(msg): report.append(msg)

    # בדיקת משתני סביבה
    log("🔍 משתני סביבה:")
    for var in ["TELEGRAM_TOKEN", "HUGGINGFACE_API_KEY"]:
        val = os.getenv(var)
        log(f"{'✅' if val else '❌'} {var} {'מוגדר' if val else '***חסר***'}")
    secret = os.getenv("WEBHOOK_SECRET_TOKEN")
    log(f"{'✅' if secret else '⚠️'} WEBHOOK_SECRET_TOKEN ({'מוגדר' if secret else 'לא חובה'})")

    # Telegram getMe
    token = os.getenv("TELEGRAM_TOKEN")
    if token:
        log("\n🔍 בדיקת Telegram:")
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getMe")
            data = r.json()
            if data.get("ok"):
                log(f"✅ Telegram פעיל (@{data['result']['username']})")
            else:
                log(f"❌ שגיאת API: {data}")
        except Exception as e:
            log(f"❌ שגיאה: {e}")

        # Webhook info
        log("\n🔍 Webhook:")
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
            data = r.json()
            if data.get("ok"):
                result = data["result"]
                log(f"📡 URL: {result.get('url', 'לא הוגדר')}")
                log(f"📨 Pending: {result.get('pending_update_count', 0)}")
                if result.get("last_error_message"):
                    log(f"❌ שגיאה אחרונה: {result['last_error_message']}")
                else:
                    log("✅ אין שגיאות אחרונות")
            else:
                log(f"❌ Webhook API error: {data}")
        except Exception as e:
            log(f"❌ שגיאה: {e}")
    else:
        log("⚠️ לא מוגדר TELEGRAM_TOKEN - לא ניתן לבדוק Webhook")

    return "<pre>" + "\n".join(report) + "</pre>", 200

# === הפעלת Gunicorn על פורט ברנדר ===
if __name__ == "__main__":
    import asyncio
    import threading

    def run_bot():
        telegram_app.run_polling()

    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
