import logging
import os
import json
import threading
from datetime import datetime
import pytz
import telebot
import google.generativeai as genai
from http.server import HTTPServer, BaseHTTPRequestHandler

# === הגדרות מאובטחות ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

print("🚀 מתחילה להפעיל את מאיה...")

# בדיקת בטיחות
if not TELEGRAM_TOKEN:
    print("❌ שגיאה: TELEGRAM_TOKEN לא הוגדר ב-Environment Variables")
    exit(1)

if not GEMINI_API_KEY:
    print("❌ שגיאה: GEMINI_API_KEY לא הוגדר ב-Environment Variables")
    exit(1)

# Setup Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini API מחובר בהצלחה")
except Exception as e:
    print(f"❌ שגיאה בחיבור ל-Gemini: {e}")
    exit(1)

# יצירת instance של הבוט
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === זיכרון ===
USER_MEMORY_FILE = 'maya_memory.json'
user_memory = {}
chat_sessions = {}

def load_memory():
    global user_memory
    try:
        if os.path.exists(USER_MEMORY_FILE):
            with open(USER_MEMORY_FILE, 'r', encoding='utf-8') as f:
                user_memory = json.load(f)
                print(f"✅ נטען זיכרון עבור {len(user_memory)} משתמשים")
    except Exception as e:
        print(f"⚠️ שגיאה בטעינת זיכרון: {e}")
        user_memory = {}

def save_memory():
    try:
        with open(USER_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_memory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f'Error saving memory: {e}')

def get_current_time_israel():
    israel_tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(israel_tz)
    return now.strftime('%H:%M:%S'), now.strftime('%A, %d %B %Y')

def create_system_prompt(user_id):
    current_time, current_date = get_current_time_israel()
    user_context = ""
    
    if str(user_id) in user_memory:
        user_context = f"זוכר עליך: {json.dumps(user_memory[str(user_id)], ensure_ascii=False)}"
    
    return f'''את מאיה - בוט טלגרם חכם, חמוד ועוזר!

🕐 זמן נוכחי: {current_time}
📅 תאריך: {current_date}
📍 מיקום: ישראל

👤 מידע על המשתמש: {user_context}

האישיות שלך:
- חמודה, ידידותית ועוזרת
- כותבת בעברית באופן טבעי
- זוכרת פרטים חשובים על המשתמשים
- עונה בצורה קצרה ולעניין (עד 2-3 שורות)
- משתמשת באמוג'ים באופן מתון
- מגיבה באופן אנושי וחם

תני תשובה מועילה וחמודה!'''

def create_chat_session(user_id):
    try:
        chat = model.start_chat(history=[])
        system_prompt = create_system_prompt(user_id)
        chat.send_message(system_prompt)
        return chat
    except Exception as e:
        logging.error(f"שגיאה ביצירת צ'אט: {e}")
        return None

# === Handler לכל ההודעות ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_id = str(message.from_user.id)
        text = message.text.strip()
        
        # יצירת צ'אט אם לא קיים
        if user_id not in chat_sessions:
            chat_sessions[user_id] = create_chat_session(user_id)
            if not chat_sessions[user_id]:
                bot.send_message(message.chat.id, "😅 סליחה, יש לי בעיה טכנית קטנה. נסה שוב בעוד רגע!")
                return
        
        # שליחת הודעת "כותבת..."
        bot.send_chat_action(message.chat.id, 'typing')
        
        # קבלת תגובה מ-Gemini
        try:
            response = chat_sessions[user_id].send_message(text)
            bot_response = response.text
        except Exception as e:
            logging.error(f"שגיאה ב-Gemini: {e}")
            bot_response = "😅 סליחה, קרתה לי שגיאה קטנה. אפשר לנסות שוב?"
            # יצירת צ'אט חדש במקרה של שגיאה
            chat_sessions[user_id] = create_chat_session(user_id)
        
        # שליחת התגובה
        bot.send_message(message.chat.id, bot_response)
        
    except Exception as e:
        logging.error(f"שגיאה כללית ב-handle_message: {e}")
        bot.send_message(message.chat.id, "😅 אופס! משהו לא עבד. בואו ננסה שוב?")

# === פקודות ===
@bot.message_handler(commands=['memory'])
def memory_command(message):
    user_id = str(message.from_user.id)
    if user_id in user_memory and user_memory[user_id]:
        memory_text = "🧠 מה שאני זוכרת עליך:\n"
        for key, value in user_memory[user_id].items():
            memory_text += f"• {key}: {value}\n"
        bot.send_message(message.chat.id, memory_text)
    else:
        bot.send_message(message.chat.id, "🤔 עדיין לא למדתי עליך הרבה. ספר לי משהו על עצמך!")

@bot.message_handler(commands=['forget'])
def forget_command(message):
    user_id = str(message.from_user.id)
    if user_id in user_memory:
        del user_memory[user_id]
        save_memory()
        bot.send_message(message.chat.id, "🧹 מחקתי את כל מה שזכרתי עליך. בואו נכיר מחדש!")
    else:
        bot.send_message(message.chat.id, "🤷‍♀️ בכל מקרה לא זכרתי עליך כלום!")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    total_users = len(user_memory)
    active_chats = len(chat_sessions)
    current_time, current_date = get_current_time_israel()
    stats_text = f"""📊 סטטיסטיקות מאיה:
👥 סך המשתמשים: {total_users}
💬 צ'אטים פעילים: {active_chats}
🕐 זמן: {current_time}
📅 תאריך: {current_date}"""
    bot.send_message(message.chat.id, stats_text)

# === שרת בריאות ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("✅ מאיה פועלת בהצלחה!".encode('utf-8'))
    
    def log_message(self, format, *args):
        # מונע הדפסת לוגים מיותרים
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"✅ שרת בריאות הופעל על פורט {port}")
    server.serve_forever()

# === הפעלה ראשית ===
def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # טעינת זיכרון
    load_memory()
    
    # הפעלת שרת הבריאות בthread נפרד
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    print('🎉 מאיה מוכנה לפעולה! שולחת אהבה ועזרה! 💚')
    
    # הפעלת הבוט
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logging.error(f"שגיאה בpolling: {e}")
        print("❌ הבוט נעצר בגלל שגיאה")

if __name__ == '__main__':
    main()
