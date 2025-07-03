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
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False)
    except Exception as e:
        print("Save error:", e)

def load_data():
    global user_data
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            user_data = json.load(f)
        print("Memory loaded for", len(user_data), "users")
    except:
        user_data = {}

def get_time_israel():
    tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(tz)
    return now.strftime("%H:%M"), now.strftime("%A %d/%m/%Y")

def extract_user_info(user_id, text):
    user_id = str(user_id)
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if "קוראים לי" in text:
        try:
            parts = text.split("קוראים לי")
            if len(parts) > 1:
                name = parts[1].strip().split()[0]
                user_data[user_id]["שם"] = name.replace(",", "").replace(".", "")
                save_data()
                return True
        except:
            pass
    return False

def quick_answers(text):
    text_lower = text.lower()
    
    if any(phrase in text_lower for phrase in ["מה השעה", "איזה שעה"]):
        time_now, _ = get_time_israel()
        return "🕐 השעה עכשיו: " + time_now
    
    if any(phrase in text_lower for phrase in ["מה התאריך", "מה היום"]):
        _, date_now = get_time_israel()
        return "📅 התאריך היום: " + date_now
    
    if "מזג אוויר" in text_lower:
        if "ניו יורק" in text_lower:
            return "🌤️ בניו יורק בחורף קר ובקיץ חם"
        elif "תל אביב" in text_lower:
            return "☀️ בתל אביב חם ושמש כמעט תמיד"
        else:
            return "🌍 איזו עיר?"
    
    return None

def create_prompt(user_id):
    time_now, date_now = get_time_israel()
    user_info = user_data.get(str(user_id), {})
    user_name = user_info.get("שם", "חבר")
    
    prompt = "את מאיה - עוזרת חכמה! זמן: " + time_now + " תאריך: " + date_now
    prompt += " המשתמש: " + user_name
    prompt += " תני תשובות קצרות וחמודות!"
    
    return prompt

def start_chat(user_id):
    try:
        chat = model.start_chat(history=[])
        prompt = create_prompt(user_id)
        chat.send_message(prompt)
        return chat
    except Exception as e:
        print("Chat error:", e)
        return None

class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Maya Running")
    def log_message(self, *args): 
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthServer)
    server.serve_forever()

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    text = message.text
    
    quick_answer = quick_answers(text)
    if quick_answer:
        bot.reply_to(message, quick_answer)
        return
    
    info_saved = extract_user_info(user_id, text)
    
    if user_id not in chats:
        chats[user_id] = start_chat(user_id)
    
    if info_saved:
        chats[user_id] = start_chat(user_id)
    
    if not chats[user_id]:
        bot.reply_to(message, "😅 בעיה טכנית")
        return
    
    try:
        bot.send_chat_action(message.chat.id, "typing")
        response = chats[user_id].send_message(text)
        bot.reply_to(message, response.text)
    except Exception as e:
        chats[user_id] = start_chat(user_id)
        bot.reply_to(message, "😅 נסה שוב")

@bot.message_handler(commands=["memory"])
def memory_cmd(message):
    user_id = str(message.from_user.id)
    info = user_data.get(user_id, {})
    if info:
        text = "🧠 זוכרת עליך:\n"
        for key, value in info.items():
            text += key + ": " + value + "\n"
        bot.reply_to(message, text)
    else:
        bot.reply_to(message, "🤔 לא זוכרת עליך הרבה")

@bot.message_handler(commands=["time"])
def time_cmd(message):
    time_now, date_now = get_time_israel()
    bot.reply_to(message, "🕐 " + time_now + "\n📅 " + date_now)

def main():
    print("Maya starting")
    
    try:
        bot.remove_webhook()
    except:
        pass
    
    load_data()
    threading.Thread(target=run_server, daemon=True).start()
    
    print("Maya ready")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print("Error:", e)
            import time
            time.sleep(5)

if __name__ == "__main__":
    main()
