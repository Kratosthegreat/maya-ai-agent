import os
import json
from flask import Flask, request
import telebot

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# נתונים לדוגמה, אפשר להרחיב כרצונך
user_data = {}
tasks = {}
contacts = {}

def load_data():
    global user_data, tasks, contacts
    try:
        with open("data.json", "r") as f:
            data = json.load(f)
            user_data = data.get("user_data", {})
            tasks = data.get("tasks", {})
            contacts = data.get("contacts", {})
    except Exception:
        user_data = {}
        tasks = {}
        contacts = {}

def save_data():
    try:
        with open("data.json", "w") as f:
            json.dump({
                "user_data": user_data,
                "tasks": tasks,
                "contacts": contacts
            }, f)
    except Exception as e:
        print("Error saving data:", e)

# דוגמה לטיפול בהודעה - אפשר להרחיב לכל לוגיקה שתרצה
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    bot.reply_to(message, "היי! קיבלתי את ההודעה: " + message.text)

# webhook מהטלגרם
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

# health check ל-Render
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

def main():
    load_data()
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()
