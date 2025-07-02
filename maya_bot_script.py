# --- מאיה - בוט טלגרם מחובר ל-GPT עם תגובות חיות ושיחות יזומות ---
import logging
import random
import asyncio
import httpx
import os
import json
from datetime import datetime, time
import pytz
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler, JobQueue
import google.generativeai as genai

# Settings
TELEGRAM_TOKEN = '7876544988:AAFZUHIzHOqyzpJ5TIec2hJFtdiawc4JMF4'
GEMINI_API_KEY = 'AIzaSyBoIvgf3WlDQj1gDfGySUOi_JXqR-8GdcM'

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
    if str(user_id) not in user_memory:
        user_memory[str(user_id)] = {
            'name': 'דוד',
            'preferences': [],
            'important_info': [],
            'last_seen': datetime.now().isoformat(),
            'conversation_count': 0
        }
    user_data = user_memory[str(user_id)]
    user_data['last_seen'] = datetime.now().isoformat()
    user_data['conversation_count'] += 1
    if new_info:
        if new_info not in user_data['important_info']:
            user_data['important_info'].append(new_info)
            if len(user_data['important_info']) > 10:
                user_data['important_info'] = user_data['important_info'][-10:]
    save_memory(user_memory)

def get_user_context(user_id):
    user_data = user_memory.get(str(user_id), {})
    if not user_data:
        return 'משתמש חדש'
    context = f'שם: {user_data.get("name", "דוד")}\n'
    context += f'מספר שיחות: {user_data.get("conversation_count", 0)}\n'
    if user_data.get('important_info'):
        context += 'דברים שאני זוכרת עליך:\n'
        for info in user_data['important_info'][-5:]:
            context += f'• {info}\n'
    return context

def create_enhanced_system_prompt(user_id):
    current_time, current_date, _ = get_current_time_israel()
    user_context = get_user_context(user_id)
    return f'''את מאיה, המזכירה האישית והחברה הטובה של דוד. 

זמן עכשיו: {current_time}, {current_date}

על המשתמש:
{user_context}

האישיות שלך:
• תדברי כמו חברה אמיתית, לא כמו רובוט
• תהיי מעניינת, שובבה ומצחיקה לפעמים
• תזכרי דברים ותתייחסי אליהם
• תשאלי שאלות כדי להכיר אותו יותר
• תהיי אמוזמת וטבעית

מה שאת יכולה:
✅ לזכור מה שהוא אומר לך
✅ להכיר אותו יותר עם הזמן
✅ לתת שעה ומזג אוויר
✅ לעזור בכל מה שהוא צריך

דרך דיבור:
• "היי דוד" במקום "שלום משתמש"
• "זוכרת שאמרת לי ש..." 
• "איך הלך לך עם...?"
• תהיי טבעית ולא פורמלית

תהיי מאיה - החברה שבאמת מכירה אותו!'''

def create_chat_session(user_id):
    chat = model.start_chat(history=[])
    system_prompt = create_enhanced_system_prompt(user_id)
    chat.send_message(system_prompt)
    return chat

def extract_important_info(message):
    keywords = ['אני אוהב', 'אני עובד', 'אני גר', 'המשפחה שלי', 'אני לומד', 'החברה שלי']
    for keyword in keywords:
        if keyword in message.lower():
            return message
    return None

personal_responses = [
    'היי דוד! מה המצב שלך?',
    'אהלן חביבי! איך היום?',
    'דוד! מה קורה איתך?',
    'שלום לך! איך החיים מתנהלים?',
    'היי יקר! מה חדש אצלך?'
]

def is_quick_message(msg):
    return msg.lower().strip() in ['היי', 'היי מאיה', 'מאיה', 'מה קורה', 'את פה', 'נו', 'שלום', 'מה המצב', 'בוקר טוב']

async def respond(update, context):
    user_message = update.message.text.strip()
    chat_id = update.message.chat_id
    user_id = update.effective_user.id

    important_info = extract_important_info(user_message)
    update_user_memory(user_id, important_info)

    if is_quick_message(user_message):
        current_time, current_date, _ = get_current_time_israel()
        user_data = user_memory.get(str(user_id), {})
        conv_count = user_data.get('conversation_count', 0)
        if conv_count > 5:
            reply = random.choice([
                f'היי דוד! שמחה לראות אותך שוב 😊',
                f'אהלן! איך הלכו לך הדברים מאז שדיברנו?',
                f'דוד! נפגשנו שוב! מה המצב?'
            ])
        else:
            reply = random.choice(personal_responses)
        reply += f'\n\n🕐 {current_time} | 📅 {current_date}'
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    if any(word in user_message.lower() for word in ['שעה', 'זמן', 'מתי', 'איזה שעה']):
        current_time, current_date, _ = get_current_time_israel()
        reply = f'🕐 השעה עכשיו: {current_time}\n📅 {current_date}'
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    if any(word in user_message.lower() for word in ['מזג אוויר', 'טמפרטורה', 'חם', 'קר', 'גשם', 'מזג']):
        reply = 'לא חיברנו עדיין מזג אוויר כאן 🌀'
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = create_chat_session(user_id)

    try:
        current_time, current_date, _ = get_current_time_israel()
        user_context = get_user_context(user_id)
        enhanced_message = f'''דוד אמר: "{user_message}"

מה שאני זוכרת על דוד:
{user_context}

זמן עכשיו: {current_time}, {current_date}

תני תשובה אישית, טבעית וחברותית. תתייחסי למה שאת זוכרת עליו.'''
        chat_session = chat_sessions[chat_id]
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: chat_session.send_message(enhanced_message))
        reply = response.text
        await context.bot.send_message(chat_id=chat_id, text=reply)
    except Exception as e:
        logging.error(f'Error: {e}')
        await context.bot.send_message(chat_id=chat_id, text='יש לי תקלה קטנה... תנסה שוב?')

async def morning_message(context: ContextTypes.DEFAULT_TYPE):
    for user_id in user_memory:
        name = user_memory[user_id].get("name", "דוד")
        text = f"☀️ בוקר טוב {name}! איך ישנת? אני פה אם אתה צריך משהו להיום 😊"
        await context.bot.send_message(chat_id=int(user_id), text=text)

async def reminder_message(context: ContextTypes.DEFAULT_TYPE):
    for user_id in user_memory:
        text = "היי! רק רציתי להזכיר לך לשתות מים, לנשום רגע... ואולי גם לעשות משהו קטן בשביל עצמך עכשיו. 💧🧘"
        await context.bot.send_message(chat_id=int(user_id), text=text)

async def memory_command(update, context):
    user_id = update.effective_user.id
    user_context = get_user_context(user_id)
    reply = f'🧠 מה שאני זוכרת עליך:\n\n{user_context}'
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def forget_command(update, context):
    user_id = update.effective_user.id
    global user_memory
    if str(user_id) in user_memory:
        del user_memory[str(user_id)]
        save_memory(user_memory)
        reply = 'שכחתי הכל עליך! נתחיל מחדש 🧹'
    else:
        reply = 'ממילא לא זכרתי עליך כלום 😅'
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def stats_command(update, context):
    total_users = len(user_memory)
    total_conversations = sum(data.get('conversation_count', 0) for data in user_memory.values())
    reply = f'''📊 הסטטיסטיקות שלי:

👥 משתמשים שאני מכירה: {total_users}
💬 סה"כ שיחות: {total_conversations}
🧠 פועלת מאז: השבוע

אני לומדת ומשתפרת כל הזמן! 🚀'''
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    app.add_handler(CommandHandler('memory', memory_command))
    app.add_handler(CommandHandler('forget', forget_command))
    app.add_handler(CommandHandler('stats', stats_command))

    job_queue = app.job_queue
    job_queue.run_daily(morning_message, time=time(8, 0, tzinfo=pytz.timezone('Asia/Jerusalem')))
    job_queue.run_daily(reminder_message, time=time(13, 0, tzinfo=pytz.timezone('Asia/Jerusalem')))

    print('🚀 מאיה חיה, זוכרת ויוזמת 😄')
    app.run_polling()

if __name__ == '__main__':
    main()
