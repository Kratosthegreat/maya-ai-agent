import logging
import random
import asyncio
import httpx
import os
import json
from datetime import datetime, timedelta, time
import pytz
from telegram import Update, Bot
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler
from telegram.ext import JobQueue
import google.generativeai as genai
import threading

# === הגדרות מאובטחות ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# בדיקת בטיחות - וידוא שהטוקנים קיימים
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

# קובץ זיכרון
USER_MEMORY_FILE = 'maya_memory.json'

# === פונקציות זיכרון ===
def load_memory():
    try:
        if os.path.exists(USER_MEMORY_FILE):
            with open(USER_MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ נטען זיכרון עבור {len(data)} משתמשים")
                return data
    except Exception as e:
        print(f"⚠️ שגיאה בטעינת זיכרון: {e}")
    return {}

def save_memory(memory_data):
    try:
        with open(USER_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f'Error saving memory: {e}')

user_memory = load_memory()
chat_sessions = {}

# === פונקציות עזר ===
def get_current_time_israel():
    israel_tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(israel_tz)
    return now.strftime('%H:%M:%S'), now.strftime('%A, %d %B %Y'), now

async def get_weather_data(city='תל אביב'):
    try:
        # כאן תוכל להוסיף API לmזג אוויר בעתיד
        return f"מזג האוויר ב{city}: נתונים לא זמינים כרגע"
    except:
        return None

def update_user_memory(user_id, new_info):
    user_id = str(user_id)
    if user_id not in user_memory:
        user_memory[user_id] = {}
    
    if new_info:
        user_memory[user_id].update(new_info)
        save_memory(user_memory)

def get_user_context(user_id):
    user_id = str(user_id)
    if user_id in user_memory:
        return f"זוכר עליך: {json.dumps(user_memory[user_id], ensure_ascii=False)}"
    return ""

def create_enhanced_system_prompt(user_id):
    current_time, current_date, _ = get_current_time_israel()
    user_context = get_user_context(user_id)
    
    return f'''את מאיה - בוט טלגרם חכם, חמוד ועוזר!

🕐 זמן נוכחי: {current_time}
📅 תאריך: {current_date}
📍 מיקום: ישראל

👤 מידע על המשתמש: {user_context}

האישיות שלך:
- חמודה, ידידותית ועוזרת
- כותבת בעברית באופן טבעי
- זוכרת פרטים חשובים על המשתמשים
- עונה בצורה קצרה ולעניין
- משתמשת באמוג'ים באופן מתון
- מגיבה באופן אנושי וחם

כשמישהו שואל אותך משהו - תני תשובה מועילה וחמודה!'''

def create_chat_session(user_id):
    try:
        chat = model.start_chat(history=[])
        system_prompt = create_enhanced_system_prompt(user_id)
        response = chat.send_message(system_prompt)
        return chat
    except Exception as e:
        logging.error(f"שגיאה ביצירת צ'אט: {e}")
        return None

def extract_important_info(message):
    # זיהוי פרטים חשובים בהודעה
    important_patterns = {
        'name': r'קוראים לי|השם שלי|אני|שמי',
        'age': r'בן|בת|גיל|שנים',
        'location': r'גר|גרה|בעיר|ממ',
        'work': r'עובד|עובדת|עבודה|מקצוע'
    }
    # כאן תוכל להוסיף לוגיקה לזיהוי פרטים
    return None

def is_quick_message(msg):
    quick_messages = [
        'היי', 'היי מאיה', 'מאיה', 'מה קורה', 'את פה', 
        'נו', 'שלום', 'מה המצב', 'בוקר טוב', 'לילה טוב',
        'תודה', 'תודה רבה', 'יופי', 'מעולה'
    ]
    return msg.lower().strip() in quick_messages

# === פונקציית התגובה הראשית ===
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        message = update.message.text.strip()
        
        # יצירת צ'אט אם לא קיים
        if user_id not in chat_sessions:
            chat_sessions[user_id] = create_chat_session(user_id)
            if not chat_sessions[user_id]:
                await update.message.reply_text("😅 סליחה, יש לי בעיה טכנית קטנה. נסה שוב בעוד רגע!")
                return
        
        # שליחת הודעת "כותבת..."
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # קבלת תגובה מ-Gemini
        try:
            response = chat_sessions[user_id].send_message(message)
            bot_response = response.text
        except Exception as e:
            logging.error(f"שגיאה ב-Gemini: {e}")
            bot_response = "😅 סליחה, קרתה לי שגיאה קטנה. אפשר לנסות שוב?"
            # יצירת צ'אט חדש במקרה של שגיאה
            chat_sessions[user_id] = create_chat_session(user_id)
        
        # עדכון זיכרון המשתמש
        new_info = extract_important_info(message)
        if new_info:
            update_user_memory(user_id, new_info)
        
        # שליחת התגובה
        await update.message.reply_text(bot_response)
        
    except Exception as e:
        logging.error(f"שגיאה כללית ב-respond: {e}")
        await update.message.reply_text("😅 אופס! משהו לא עבד. בואו ננסה שוב?")

# === הודעות יזומות ===
async def morning_message(context: ContextTypes.DEFAULT_TYPE):
    try:
        for user_id in user_memory:
            try:
                name = user_memory[user_id].get("name", "חבר")
                text = f"☀️ בוקר טוב {name}! איך ישנת? אני פה אם אתה צריך משהו להיום 😊"
                await context.bot.send_message(chat_id=int(user_id), text=text)
            except Exception as e:
                logging.error(f"שגיאה בשליחת הודעת בוקר למשתמש {user_id}: {e}")
    except Exception as e:
        logging.error(f"שגיאה כללית בהודעת בוקר: {e}")

async def reminder_message(context: ContextTypes.DEFAULT_TYPE):
    try:
        reminders = [
            "היי! רק רציתי להזכיר לך לשתות מים 💧",
            "זמן לנשום עמוק ולהירגע רגע 🧘‍♀️",
            "מה דעתך לעשות משהו קטן ונחמד בשביל עצמך? ☺️",
            "רק רציתי לבדוק איך אתה מרגיש היום 🌸"
        ]
        
        for user_id in user_memory:
            try:
                text = random.choice(reminders)
                await context.bot.send_message(chat_id=int(user_id), text=text)
            except Exception as e:
                logging.error(f"שגיאה בשליחת תזכורת למשתמש {user_id}: {e}")
    except Exception as e:
        logging.error(f"שגיאה כללית בתזכורת: {e}")

# === פקודות ===
async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in user_memory and user_memory[user_id]:
        memory_text = "🧠 מה שאני זוכרת עליך:\n"
        for key, value in user_memory[user_id].items():
            memory_text += f"• {key}: {value}\n"
        await update.message.reply_text(memory_text)
    else:
        await update.message.reply_text("🤔 עדיין לא למדתי עליך הרבה. ספר לי משהו על עצמך!")

async def forget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in user_memory:
        del user_memory[user_id]
        save_memory(user_memory)
        await update.message.reply_text("🧹 מחקתי את כל מה שזכרתי עליך. בואו נכיר מחדש!")
    else:
        await update.message.reply_text("🤷‍♀️ בכל מקרה לא זכרתי עליך כלום!")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(user_memory)
    active_chats = len(chat_sessions)
    stats_text = f"""📊 סטטיסטיקות מאיה:
👥 סך המשתמשים: {total_users}
💬 צ'אטים פעילים: {active_chats}
🕐 זמן: {get_current_time_israel()[0]}
📅 תאריך: {get_current_time_israel()[1]}"""
    await update.message.reply_text(stats_text)

# === שרת בריאות פשוט (Health Check) ===
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Maya Bot is running!")
    
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
    
    print("🚀 מתחילה להפעיל את מאיה...")

    # ניקוי webhook קיים למניעת קונפליקטים
    async def reset_webhook():
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook נוקה בהצלחה")
        except Exception as e:
            print(f"⚠️ שגיאה בניקוי webhook: {e}")
    
    # יצירת event loop חדש לPython 3.13
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(reset_webhook())

    # הפעלת שרת הבריאות בthread נפרד
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    # בניית האפליקציה
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # הוספת handlers
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    app.add_handler(CommandHandler('memory', memory_command))
    app.add_handler(CommandHandler('forget', forget_command))
    app.add_handler(CommandHandler('stats', stats_command))

    # הוספת משימות מתוזמנות
    try:
        if app.job_queue:
            # הודעת בוקר יומית ב-8:00
            app.job_queue.run_daily(
                morning_message, 
                time=time(8, 0, 0, tzinfo=pytz.timezone('Asia/Jerusalem'))
            )
            
            # תזכורת אחה"צ ב-14:00
            app.job_queue.run_daily(
                reminder_message, 
                time=time(14, 0, 0, tzinfo=pytz.timezone('Asia/Jerusalem'))
            )
            
            print("✅ משימות מתוזמנות הופעלו")
        else:
            print("⚠️ JobQueue לא זמין")
    except Exception as e:
        print(f"⚠️ שגיאה במשימות מתוזמנות: {e}")

    print('🎉 מאיה מוכנה לפעולה! שולחת אהבה ועזרה! 💚')
    
    # הפעלת הבוט עם event loop מתאים
    try:
        app.run_polling(drop_pending_updates=True)
    except RuntimeError as e:
        if "event loop" in str(e):
            # פתרון לPython 3.13
            async def run_bot():
                await app.initialize()
                await app.start()
                await app.updater.start_polling(drop_pending_updates=True)
                await app.updater.idle()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_bot())
        else:
            raise e

if __name__ == '__main__':
    main()
