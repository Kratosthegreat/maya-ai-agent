import os
import json
import threading
from datetime import datetime
import pytz
import telebot
import google.generativeai as genai
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("Missing tokens")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_data = {}
chats = {}

def save_data():
    try:
        with open("data.json", "w") as f:
            json.dump(user_data, f)
    except:
        pass

def load_data():
    global user_data
    try:
        with open("data.json", "r") as f:
            user_data = json.load(f)
    except:
        user_data = {}

def get_time():
    tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(tz)
    return now.strftime("%H:%M")

def quick_answers(text):
    if "מה השעה" in text.lower():
        return "🕐 השעה עכשיו: " + get_time()
    return None

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    quick = quick_answers(message.text)
    if quick:
        bot.reply_to(message, quick)
    else:
        bot.reply_to(message, "אני עובדת!")

class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args): 
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthServer).serve_forever()

def main():
    threading.Thread(target=run_server, daemon=True).start()
    bot.polling()

if __name__ == "__main__":
    main()
