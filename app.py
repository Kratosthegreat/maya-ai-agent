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

# === הכנת Telegram Application ללא polling/updater ===
telegram_app = (
    ApplicationBuilder()
    .token(TELEGRAM_TOKEN)
    .updater(None)
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

# === דיאגנוסטיקה כללית ===
@app.route("/diagnose", methods=["GET"])
def diagnose():
    report = []
    def log(line): report.append(line)

    log("🩺 דיאגנוסטיקה כללית למאיה ב־Render\n")

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

# === דיאגנוסטיקה OpenRouter ===
@app.route("/diagnose/openrouter", methods=["GET"])
def diagnose_openrouter():
    report = []
    def log(line): report.append(line)

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    log("🛠 דיאגנוסטיקה OpenRouter\n")
    log(f"{'✅' if OPENROUTER_API_KEY else '❌'} OPENROUTER_API_KEY: {'מוגדר' if OPENROUTER_API_KEY else '***חסר***'}")

    if OPENROUTER_API_KEY:
        # בדיקה בסיסית של חיבור OpenRouter (לדוגמה, בדיקת סטטוס API)
        try:
            # כאן דוגמה לבקשה פשוטה - שנה לפי API אמיתי
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            r = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=5)
            if r.status_code == 200:
                log("✅ חיבור OpenRouter תקין, קיבל תגובה 200")
            else:
                log(f"❌ שגיאה בקבלת מודלים, סטטוס קוד: {r.status_code}")
        except Exception as e:
            log(f"❌ שגיאת חיבור OpenRouter: {e}")
    else:
        log("🚫 לא ניתן לבדוק OpenRouter – טוקן חסר")

    return "<pre>" + "\n".join(report) + "</pre>", 200

# === דיאגנוסטיקה Telegram מפורטת ===
@app.route("/diagnose/telegram", methods=["GET"])
def diagnose_telegram():
    report = []
    def log(line): report.append(line)

    log("📡 דיאגנוסטיקה Telegram\n")

    if TELEGRAM_TOKEN:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe")
            data = r.json()
            if data.get("ok"):
                username = data['result']['username']
                log(f"✅ בוט פעיל (@{username})")
            else:
                log(f"❌ שגיאה ב-getMe: {data}")
        except Exception as e:
            log(f"❌ שגיאת getMe: {e}")

        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo")
            data = r.json()
            if data.get("ok"):
                result = data["result"]
                log(f"🌐 URL: {result.get('url', 'לא הוגדר')}")
                log(f"📨 ממתינים לעדכונים: {result.get('pending_update_count', 0)}")
                last_err = result.get("last_error_message")
                if last_err:
                    log(f"❌ שגיאה אחרונה: {last_err}")
                else:
                    log("✅ אין שגיאות פעילות")
            else:
                log(f"❌ שגיאה ב-getWebhookInfo: {data}")
        except Exception as e:
            log(f"❌ שגיאת WebhookInfo: {e}")
    else:
        log("🚫 טוקן טלגרם לא מוגדר, לא ניתן לבדוק")

    return "<pre>" + "\n".join(report) + "</pre>", 200

# === דיאגנוסטיקה זיכרון/DB (דוגמה) ===
@app.route("/diagnose/memory", methods=["GET"])
def diagnose_memory():
    report = []
    def log(line): report.append(line)

    log("🧠 דיאגנוסטיקה זיכרון / DB\n")

    # כאן דוגמה לבדיקה - תחליף לפי מה שמתאים אצלך
    try:
        # נניח שיש DB או זיכרון פנימי לבדיקה
        memory_healthy = True  # שנה לפי לוגיקה אמיתית
        if memory_healthy:
            log("✅ מצב זיכרון תקין")
        else:
            log("❌ בעיה בזיכרון פנימי")
    except Exception as e:
        log(f"❌ שגיאה בבדיקת זיכרון: {e}")

    return "<pre>" + "\n".join(report) + "</pre>", 200


if __name__ == "__main__":
    app.run(debug=True)
