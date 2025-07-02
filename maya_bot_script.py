import os
import json
import threading
from datetime import datetime
import pytz
import telebot
import google.generativeai as genai
from http.server import HTTPServer, BaseHTTPRequestHandler

# הגדרות
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# בדיקות בטיחות
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("❌ חסרים טוקנים!")
    exit(1)

# הגדרת Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# יצירת הבוט
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# זיכרון
user_data = {}
chats = {}

def save_data():
    try:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False)
    except:
        pass

def load_data():
    global user_data
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    except:
        user_data = {}

def get_time():
    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    return now.strftime('%H:%M'), now.strftime('%A %d/%m/%Y')

def create_prompt(user_id):
    time_now, date_now = get_time()
    user_info = user_data.get(str(user_id), {})
    
    prompt = f"""את מאיה - עוזרת אישית חכמה וחמודה! 🌟

זמן עכשיו: {time_now}
תאריך: {date_now}
מקום: ישראל

מידע על המשתמש: {json.dumps(user_info, ensure_ascii=False) if user_info else 'משתמש חדש'}

הוראות חשובות:
1. תני תשובות חכמות ומועילות בעברית
2. השתמשי במידע שיש לך על המשתמש
3. תשובות קצרות (1-3 שורות)
4. תני עצות אמיתיות ופתרונות מעשיים
5. שאלי שאלות המשך אם רלוונטי
6. זכרי פרטים חשובים שהמשתמש אומר

תגיבי בצורה אישית וחכמה!"""
    
    return prompt

def start_chat(user_id):
    try:
        chat = model.start_chat(history=[])
        prompt = create_prompt(user_id)
        chat.send_message(prompt)
        return chat
    except:
        return None

# שרת בריאות
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Maya Bot Running!")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthServer)
    server.serve_forever()

# טיפול בהודעות
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    text = message.text
    
    # יצירת צ'אט חדש אם צריך
    if user_id not in chats:
        chats[user_id] = start_chat(user_id)
    
    if not chats[user_id]:
        bot.reply_to(message, "😅 יש לי בעיה טכנית, נסה שוב!")
        return
    
    # שמירת מידע חשוב
    if user_id not in user_data:
        user_data[user_id] = {}
    
    # זיהוי שם
    if 'קוראים לי' in text or 'השם שלי' in text:
        words = text.split()
        for i, word in enumerate(words):
            if word in ['לי', 'שלי'] and i + 1 < len(words):
                user_data[user_id]['שם'] = words[i + 1]
                save_data()
                break
    
    # זיהוי עבודה
    if any(word in text for word in ['עובד', 'עובדת', 'עבודה']):
        user_data[user_id]['עבודה'] = text[:50]
        save_data()
    
    try:
        # שליחת typing
        bot.send_chat_action(message.chat.id, 'typing')
        
        # קבלת תגובה
        response = chats[user_id].send_message(text)
        bot.reply_to(message, response.text)
        
    except Exception as e:
        # אם יש שגיאה, ננסה צ'אט חדש
        chats[user_id] = start_chat(user_id)
        bot.reply_to(message, "😅 רגע, אני מתרעננת... נסה שוב!")

# פקודות
@bot.message_handler(commands=['memory'])
def memory_cmd(message):
    user_id = str(message.from_user.id)
    info = user_data.get(user_id, {})
    if info:
        text = "🧠 מה שאני זוכרת עליך:\n"
        for key, value in info.items():
            text += f"• {key}: {value}\n"
        bot.reply_to(message, text)
    else:
        bot.reply_to(message, "🤔 עדיין לא זכרתי עליך הרבה. ספר לי על עצמך!")

@bot.message_handler(commands=['forget'])
def forget_cmd(message):
    user_id = str(message.from_user.id)
    if user_id in user_data:
        del user_data[user_id]
        save_data()
    if user_id in chats:
        del chats[user_id]
    bot.reply_to(message, "🧹 שכחתי הכל עליך! בואו נכיר מחדש!")

@bot.message_handler(commands=['refresh'])
def refresh_cmd(message):
    user_id = str(message.from_user.id)
    chats[user_id] = start_chat(user_id)
    bot.reply_to(message, "🔄 רעננתי את הזיכרון! עכשיו אני חכמה יותר!")

def main():
    print("🚀 מאיה מתחילה...")
    
    # טעינת נתונים
    load_data()
    print(f"✅ נטען זיכרון עבור {len(user_data)} משתמשים")
    
    # הפעלת שרת
    threading.Thread(target=run_server, daemon=True).start()
    print("✅ שרת בריאות רץ")
    
    print("🎉 מאיה מוכנה!")
    
    # הפעלת הבוט
    bot.polling(none_stop=True, interval=0, timeout=20)

if __name__ == '__main__':
    main()
