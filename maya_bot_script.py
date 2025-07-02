# --- מאיה - בוט טלגרם מחובר ל-GPT עם תגובות חיות ושיחות יזומות ---
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
import weakref

# Settings
TELEGRAM_TOKEN = '7876544988:AAFZUHIzHOqyzpJ5TIec2hJFtdiawc4JMF4'
GEMINI_API_KEY = 'AIzaSyBoIvgf3WlDQj1gDfGySUOi_JxqR-8GdcM'

# Setup Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# קובץ זיכרון
USER_MEMORY_FILE = 'maya_memory.json'

# טוען זיכרון קיים
def load_memory():
    try:
        if os.path.exists(USER_MEMORY_FILE):
            with open(USER_MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

# שומר זיכרון
def save_memory(memory_data):
    try:
        with open(USER_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f'Error saving memory: {e}')

user_memory = load_memory()
chat_sessions = {}

def get_current_time_israel():
    israel_tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(israel_tz)
    return now.strftime('%H:%M:%S'), now.strftime('%A, %d %B %Y'), now

async def get_weather_data(city='תל אביב'):
    return None

def update_user_memory(user_id, new_info):
    save_memory(user_memory)

def get_user_context(user_id):
    return ""

def create_enhanced_system_prompt(user_id):
    return f'''את מאיה...'''

def create_chat_session(user_id):
    chat = model.start_chat(history=[])
    system_prompt = create_enhanced_system_prompt(user_id)
    chat.send_message(system_prompt)
    return chat

def extract_important_info(message):
    return None

personal_responses = []

def is_quick_message(msg):
    return msg.lower().strip() in ['היי', 'היי מאיה', 'מאיה', 'מה קורה', 'את פה', 'נו', 'שלום', 'מה המצב', 'בוקר טוב']

async def respond(update, context):
    pass

# --- הודעות יזומות: בוקר טוב, תזכורות וכו' ---
async def morning_message(context: ContextTypes.DEFAULT_TYPE):
    for user_id in user_memory:
        name = user_memory[user_id].get("name", "דוד")
        text = f"☀️ בוקר טוב {name}! איך ישנת? אני פה אם אתה צריך משהו להיום 😊"
        await context.bot.send_message(chat_id=int(user_id), text=text)

async def reminder_message(context: ContextTypes.DEFAULT_TYPE):
    for user_id in user_memory:
        text = "היי! רק רציתי להזכיר לך לשתות מים, לנשום רגע... ואולי גם לעשות משהו קטן בשביל עצמך עכשיו. 💧🧘"
        await context.bot.send_message(chat_id=int(user_id), text=text)

# --- פקודות ---
async def memory_command(update, context):
    pass

async def forget_command(update, context):
    pass

async def stats_command(update, context):
    pass

# --- הרצה ---
def main():
    logging.basicConfig(level=logging.INFO)

    # מנקה webhook קיים כדי למנוע שגיאת Conflict
    async def reset_webhook():
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.delete_webhook(drop_pending_updates=True)
    asyncio.run(reset_webhook())

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    app.add_handler(CommandHandler('memory', memory_command))
    app.add_handler(CommandHandler('forget', forget_command))
    app.add_handler(CommandHandler('stats', stats_command))

    try:
        job_queue = JobQueue()
        job_queue.set_application(app)
        job_queue.run_daily(morning_message, time=time(8, 0, 0, tzinfo=pytz.timezone('Asia/Jerusalem')))
        job_queue.run_daily(reminder_message, time=time(13, 0, 0, tzinfo=pytz.timezone('Asia/Jerusalem')))
        job_queue.start()
    except Exception as e:
        logging.warning(f"⚠️ JobQueue לא הופעל: {e}")

    print('🚀 מאיה חיה, זוכרת ויוזמת 😄')
    app.run_polling()

if __name__ == '__main__':
    main()
