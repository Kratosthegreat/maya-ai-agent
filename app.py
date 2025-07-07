import os
import requests
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import (
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
    .updater(None)  # נטרול ה-Updater כדי לעבוד עם Flask בלבד
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

# === דיאגנוסטיקה מתקדמת אחת מסודרת ===
@app.route("/diagnose", methods=["GET"])
def diagnose():
    report = []
    def log(line): report.append(line)

    log("🩺 דיאגנוסטיקה כללית למאיה ב־Render\n")

    # בדיקת משתנים חשובים
    log("🔐 משתני סביבה:")
    log(f"{'✅' if TELEGRAM_TOKEN else '❌'} TELEGRAM_TOKEN: {'מוגדר' if TELEGRAM_TOKEN else '***חסר***'}")
    log(f"{'✅' if WEBHOOK_SECRET_TOKEN else '⚠️'} WEBHOOK_SECRET_TOKEN: {'מוגדר' if WEBHOOK_SECRET_TOKEN else 'לא חובה'}\n")

    if TELEGRAM_TOKEN:
        try:
            log("🤖 בדיקת getMe:")
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe")
            data = r.json()
            if data.get("ok"):
                log(f"✅ בוט פעיל (@{data['result']['username']})")
            else:
                log(f"❌ שגיאה: {data}")
        except Exception as e:
            log(f"❌ שגיאת בקשת getMe: {e}")

        try:
            log("\n🔗 בדיקת Webhook:")
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo")
            data = r.json()
            if data.get("ok"):
                result = data["result"]
                log(f"🌐 כתובת: {result.get('url', 'לא הוגדר')}")
                log(f"📨 ממתינים: {result.get('pending_update_count', 0)}")
                if result.get("last_error_message"):
                    log(f"❌ שגיאה אחרונה: {result['last_error_message']}")
                else:
                    log("✅ אין שגיאות פעילות")
            else:
                log(f"❌ שגיאה ב־getWebhookInfo: {data}")
        except Exception as e:
            log(f"❌ שגיאת Webhook: {e}")
    else:
        log("🚫 לא ניתן לבדוק את הבוט – טוקן חסר")

    return "<pre>" + "\n".join(report) + "</pre>", 200

if __name__ == "__main__":
    app.run(debug=True)
