import os
import json
from datetime import datetime
import pytz
import telebot
from flask import Flask, request

# ... (כל שאר הקוד שלך: user_data, save_data, load_data, הפונקציות של המזכירה החכמה וכו')

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # לדוג' https://your-app-name.onrender.com/
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === Flask App for Webhook ===
app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

@app.route("/", methods=["GET"])
def health():  # Health check endpoint
    return "OK", 200

# === הפעלת webhook ===
def main():
    load_data()
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()
