import os
import requests
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# === משתני סביבה ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")

# === Flask ===
app = Flask(__name__)

# === הכנת Application ללא polling/updater ===
telegram_app = (
    ApplicationBuilder()
    .token(TELEGRAM_TOKEN)
    .updater(None)  # חשוב! נטרול ה-Updater כדי לעבוד עם Flask בלבד
    .build()
)

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("היי! אני מאיה 😊 איך אפשר לעזור?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("קיבלתי אותך. בקרוב אענה בצורה חכמה יותר 😉")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Webhook route ===
@app.route("/webhook", methods=["POST"])
def webhook():
    if WEBHOOK_SECRET_TOKEN:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if token != WEBHOOK_SECRET_TOKEN:
            abort(403)

    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200

# === דיאגנוסטיקה ===
@app.route("/diagnose", methods=["GET"])
def diagnose():
    report = []
    def log(msg): report.append(msg)

    log("🔍 משתני סביבה:")
    for var in ["TELEGRAM_TOKEN"]:
        val = os.getenv(var)
        log(f"{'✅' if val else '❌'} {var} {'מוגדר' if val else '***חסר***'}")
    secret = os.getenv("WEBHOOK_SECRET_TOKEN")
    log(f"{'✅' if secret else '⚠️'} WEBHOOK_SECRET_TOKEN ({'מוגדר' if secret else 'לא חובה'})")

    token = TELEGRAM_TOKEN
    if token:
        log("\n🔍 Telegram getMe:")
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getMe")
            data = r.json()
            if data.get("ok"):
                log(f"✅ Telegram פעיל (@{data['result']['username']})")
            else:
                log(f"❌ שגיאת API: {data}")
        except Exception as e:
            log(f"❌ שגיאה: {e}")

        log("\n🔍 Webhook Info:")
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
            data = r.json()
            if data.get("ok"):
                result = data["result"]
                log(f"📡 URL: {result.get('url', 'לא הוגדר')}")
                log(f"📨 Pending: {result.get('pending_update_count', 0)}")
                err = result.get("last_error_message")
                if err:
                    log(f"❌ שגיאה אחרונה: {err}")
                else:
                    log("✅ אין שגיאות אחרונות")
            else:
                log(f"❌ שגיאת Webhook API: {data}")
        except Exception as e:
            log(f"❌ שגיאה: {e}")

    return "<pre>" + "\n".join(report) + "</pre>", 200
