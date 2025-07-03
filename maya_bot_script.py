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
    except Exception as e:
        print("Error saving data:", e)

def load_data():
    global user_data
    try:
        with open("data.json", "r") as f:
            user_data = json.load(f)
    except Exception:
        user_data = {}

def get_time():
    tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(tz)
    return now.strftime("%H:%M")

def quick_answers(text):
    """Return instant answers for certain questions without LLM call."""
    if "מה השעה" in text.lower():
        return "🕐 השעה עכשיו: " + get_time()
    return None

def ask_gemini(prompt, user_id=None):
    """Ask Gemini model for answer, optionally with context."""
    # Use chat context, if desired, for smarter conversation
    history = []
    if user_id:
        history = user_data.get(str(user_id), [])
        # Optionally limit history length
        if len(history) > 5:
            history = history[-5:]
    # Build context string
    context = ""
    for turn in history:
        context += f"User: {turn['user']}\nBot: {turn['bot']}\n"
    context += f"User: {prompt}\nBot:"
    try:
        response = model.generate_content(context)
        answer = response.text if hasattr(response, 'text') else str(response)
        # Save new turn
        if user_id:
            user_data.setdefault(str(user_id), []).append({"user": prompt, "bot": answer})
            save_data()
        return answer
    except Exception as e:
        print("Gemini error:", e)
        return "מצטערת, הייתה בעיה בעיבוד הבקשה. נסה שוב."

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    """Main message handler."""
    quick = quick_answers(message.text)
    if quick:
        bot.reply_to(message, quick)
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        answer = ask_gemini(message.text, user_id=message.from_user.id)
        bot.reply_to(message, answer)

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
    load_data()
    threading.Thread(target=run_server, daemon=True).start()
    bot.polling()

if __name__ == "__main__":
    main()
