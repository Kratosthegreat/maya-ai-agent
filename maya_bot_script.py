import logging
import random
import asyncio
import httpx
import os
import json
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler
import google.generativeai as genai

# Settings
TELEGRAM_TOKEN = '7876544988:AAFZUHIzHOqyzpJ5TIec2hJFtdiawc4JMF4'
GEMINI_API_KEY = 'AIzaSyBoIvgf3WlDQj1gDfGySUOi_JXqR-8GdcM'

# Setup Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# זיכרון קבוע - ישרוד restarts
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

# זיכרון גלובלי
user_memory = load_memory()
chat_sessions = {}

def get_current_time_israel():
    israel_tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(israel_tz)
    return now.strftime('%H:%M:%S'), now.strftime('%A, %d %B %Y'), now

async def get_weather_data(city='תל אביב'):
    try:
        city_coords = {
            'תל אביב': (32.0853, 34.7818),
            'ירושלים': (31.7683, 35.2137),
            'חיפה': (32.7940, 34.9896),
            'באר שבע': (31.2518, 34.7915),
            'עפולה': (32.6098, 35.2897),
            'נתניה': (32.3215, 34.8532)
        }
        
        city_lower = city.lower()
        matched_city = 'תל אביב'
        matched_coords = city_coords['תל אביב']
        
        for city_name, coords in city_coords.items():
            if city_lower in city_name.lower() or city_name.lower() in city_lower:
                matched_city = city_name
                matched_coords = coords
                break
        
        lat, lon = matched_coords
        url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Jerusalem'
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                current = data['current_weather']
                
                temp = current['temperature']
                windspeed = current['windspeed']
                
                weather_codes = {
                    0: 'שמיים בהירים', 1: 'בהיר ברובו', 2: 'חלקית מעונן',
                    3: 'מעונן', 61: 'גשם קל', 63: 'גשם בינוני', 65: 'גשם חזק'
                }
                
                description = weather_codes.get(current['weathercode'], 'מזג אוויר משתנה')
                
                return {
                    'temp': temp,
                    'windspeed': windspeed,
                    'description': description,
                    'city': matched_city
                }
    except Exception as e:
        logging.error(f'Weather error: {e}')
    return None

def update_user_memory(user_id, new_info):
    global user_memory
    
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
    
    # הוסף מידע חדש אם רלוונטי
    if new_info:
        if new_info not in user_data['important_info']:
            user_data['important_info'].append(new_info)
            # שמור רק 10 דברים אחרונים
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
        for info in user_data['important_info'][-5:]:  # 5 אחרונים
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
    '''מחלץ מידע חשוב מההודעה'''
    # דברים שכדאי לזכור
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

    # עדכון זיכרון
    important_info = extract_important_info(user_message)
    update_user_memory(user_id, important_info)

    if is_quick_message(user_message):
        current_time, current_date, _ = get_current_time_israel()
        
        # תגובה אישית על בסיס זיכרון
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

    # שעה
    if any(word in user_message.lower() for word in ['שעה', 'זמן', 'מתי', 'איזה שעה']):
        current_time, current_date, _ = get_current_time_israel()
        reply = f'🕐 השעה עכשיו: {current_time}\n📅 {current_date}'
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return
    
    # מזג אוויר
    if any(word in user_message.lower() for word in ['מזג אוויר', 'טמפרטורה', 'חם', 'קר', 'גשם', 'מזג']):
        cities = ['עפולה', 'תל אביב', 'ירושלים', 'חיפה', 'באר שבע', 'נתניה']
        requested_city = 'תל אביב'
        
        for city in cities:
            if city in user_message:
                requested_city = city
                break
        
        weather_data = await get_weather_data(requested_city)
        if weather_data:
            reply = f'🌤️ מזג האוויר ב{weather_data["city"]}:\n🌡️ {weather_data["temp"]}°C\n💨 רוח: {weather_data["windspeed"]} קמ"ש\n☁️ {weather_data["description"]}'
        else:
            reply = f'לא הצלחתי לקבל מזג אוויר עבור {requested_city}'
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    # תגובה כללית עם זיכרון
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
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: chat_session.send_message(enhanced_message)
        )
        
        reply = response.text
        await context.bot.send_message(chat_id=chat_id, text=reply)

    except Exception as e:
        logging.error(f'Error: {e}')
        await context.bot.send_message(chat_id=chat_id, text='יש לי תקלה קטנה... תנסה שוב?')

async def memory_command(update, context):
    '''הצגת מה שמאיה זוכרת'''
    user_id = update.effective_user.id
    user_context = get_user_context(user_id)
    
    reply = f'🧠 מה שאני זוכרת עליך:\n\n{user_context}'
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def forget_command(update, context):
    '''מחיקת זיכרון'''
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
    '''סטטיסטיקות מאיה'''
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
    
    print('🧠 מאיה עם זיכרון קבוע מוכנה!')
    print(f'📁 זיכרון נשמר ב: {USER_MEMORY_FILE}')
    app.run_polling()

if __name__ == '__main__':
    main()
