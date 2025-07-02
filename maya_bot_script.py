import logging
import random
import asyncio
import httpx
import os
from datetime import datetime
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

# Chat sessions
chat_sessions = {}

def get_current_time_israel():
    israel_tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(israel_tz)
    return now.strftime('%H:%M:%S'), now.strftime('%A, %d %B %Y')

async def get_weather_data(city='תל אביב'):
    try:
        city_coords = {
            'תל אביב': (32.0853, 34.7818),
            'ירושלים': (31.7683, 35.2137),
            'חיפה': (32.7940, 34.9896),
            'באר שבע': (31.2518, 34.7915),
            'עפולה': (32.6098, 35.2897),
            'נתניה': (32.3215, 34.8532),
            'אשדוד': (31.7940, 34.6436),
            'פתח תקווה': (32.0878, 34.8878),
            'ראשון לציון': (31.9730, 34.7925),
            'חולון': (32.0178, 34.7925)
        }
        
        city_lower = city.lower()
        matched_city = None
        matched_coords = None
        
        for city_name, coords in city_coords.items():
            if city_lower in city_name.lower() or city_name.lower() in city_lower:
                matched_city = city_name
                matched_coords = coords
                break
        
        if not matched_coords:
            matched_city = 'תל אביב'
            matched_coords = city_coords['תל אביב']
        
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
                    0: 'שמיים בהירים',
                    1: 'בהיר ברובו', 
                    2: 'חלקית מעונן',
                    3: 'מעונן',
                    45: 'ערפל',
                    48: 'ערפל קפוא',
                    51: 'טפטוף קל',
                    53: 'טפטוף בינוני', 
                    55: 'טפטוף חזק',
                    61: 'גשם קל',
                    63: 'גשם בינוני',
                    65: 'גשם חזק',
                    80: 'ממטרים קלים',
                    81: 'ממטרים חזקים',
                    95: 'סופת רעמים'
                }
                
                description = weather_codes.get(current['weathercode'], 'מזג אוויר משתנה')
                
                return {
                    'temp': temp,
                    'windspeed': windspeed,
                    'description': description,
                    'city': matched_city
                }
    except Exception as e:
        logging.error(f'שגיאה בקבלת מזג אוויר: {e}')
    return None

def create_enhanced_system_prompt():
    current_time, current_date = get_current_time_israel()
    
    return f'''את מאיה, המזכירה החכמה של דוד. תהיי טבעית, ידידותית ומועילה.

השעה עכשיו: {current_time}, {current_date}

מה שאת יכולה:
✅ לתת שעה מדויקת
✅ לבדוק מזג אוויר בכל עיר בישראל  
✅ לענות על שאלות ולעזור בכתיבה
✅ לזכור דברים במהלך השיחה
✅ לתת עצות וייעוץ

איך לדבר:
- תהיי חברותית וקצרה
- אל תגידי "אני מצטערת" או "לצערי"  
- תהיי ישירה ומועילה
- אל תחזרי על אותם דברים

תהיי מאיה - החברה הטובה והמועילה!'''

def create_chat_session():
    chat = model.start_chat(history=[])
    system_prompt = create_enhanced_system_prompt()
    chat.send_message(system_prompt)
    return chat

quick_replies = [
    'היי דוד! מה קורה? 😊',
    'שלום! איך אפשר לעזור?',
    'מה המצב? אני כאן בשבילך!',
    'היי! מה נעשה היום?',
    'אהלן! במה לעזור?',
]

def is_quick_message(msg):
    return msg.lower().strip() in ['היי', 'היי מאיה', 'מאיה', 'מה קורה', 'את פה', 'נו', 'שלום', 'מה המצב', 'בוקר טוב']

async def respond(update, context):
    user_message = update.message.text.strip()
    chat_id = update.message.chat_id

    if is_quick_message(user_message):
        current_time, current_date = get_current_time_israel()
        reply = random.choice(quick_replies)
        reply += f'\n\n🕐 {current_time}\n📅 {current_date}'
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    # שעה
    if any(word in user_message.lower() for word in ['שעה', 'זמן', 'מתי', 'איזה שעה']):
        current_time, current_date = get_current_time_israel()
        reply = f'🕐 השעה עכשיו: {current_time}\n📅 {current_date}'
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return
    
    # מזג אוויר
    if any(word in user_message.lower() for word in ['מזג אוויר', 'טמפרטורה', 'חם', 'קר', 'גשם', 'מזג']):
        # חיפוש עיר בהודעה
        cities = ['עפולה', 'תל אביב', 'ירושלים', 'חיפה', 'באר שבע', 'נתניה', 'אשדוד', 'פתח תקווה', 'ראשון לציון', 'חולון']
        requested_city = 'תל אביב'  # ברירת מחדל
        
        for city in cities:
            if city in user_message:
                requested_city = city
                break
        
        weather_data = await get_weather_data(requested_city)
        if weather_data:
            reply = f'🌤️ מזג האוויר ב{weather_data["city"]}:\n🌡️ {weather_data["temp"]}°C\n💨 רוח: {weather_data["windspeed"]} קמ"ש\n☁️ {weather_data["description"]}'
        else:
            reply = f'לא הצלחתי לקבל נתוני מזג אוויר עבור {requested_city} כרגע'
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    # תגובה כללית עם Gemini
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = create_chat_session()

    try:
        current_time, current_date = get_current_time_israel()
        
        # הוספת מידע עדכני להודעה אם רלוונטי
        weather_context = ''
        if any(word in user_message.lower() for word in ['מזג', 'חום', 'קר', 'טמפרטורה']):
            weather_data = await get_weather_data()
            if weather_data:
                weather_context = f'\nמזג אוויר עכשיו: {weather_data["temp"]}°C ב{weather_data["city"]}'
        
        enhanced_message = f'''דוד אמר: "{user_message}"

מידע עדכני:
- שעה: {current_time}, {current_date}{weather_context}

תני תשובה קצרה, ידידותית ומועילה. אל תחזרי על דברים.'''
        
        chat_session = chat_sessions[chat_id]
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: chat_session.send_message(enhanced_message)
        )
        
        reply = response.text
        await context.bot.send_message(chat_id=chat_id, text=reply)

    except Exception as e:
        logging.error(f'שגיאה בתגובה: {e}')
        await context.bot.send_message(chat_id=chat_id, text='יש לי תקלה קטנה... תנסה שוב?')

async def time_command(update, context):
    current_time, current_date = get_current_time_israel()
    reply = f'🕐 השעה: {current_time}\n📅 {current_date}'
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def weather_command(update, context):
    weather_data = await get_weather_data()
    if weather_data:
        reply = f'🌤️ מזג האוויר ב{weather_data["city"]}:\n🌡️ {weather_data["temp"]}°C\n💨 רוח: {weather_data["windspeed"]} קמ"ש\n☁️ {weather_data["description"]}'
    else:
        reply = 'לא ניתן לקבל נתוני מזג אוויר כרגע'
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def clear_history(update, context):
    chat_id = update.message.chat_id
    chat_sessions[chat_id] = create_chat_session()
    
    clear_messages = [
        'אוקיי! מחקתי הכל 🧹',
        'נוקה! בואו נתחיל מחדש ✨',
        'זיכרון נקי! מה נדבר עליו? 🎉'
    ]
    reply = random.choice(clear_messages)
    await context.bot.send_message(chat_id=chat_id, text=reply)

async def info_command(update, context):
    current_time, current_date = get_current_time_israel()
    
    info_text = f'''🤖 מאיה - המזכירה החכמה שלך

🕐 זמן עדכני: {current_time}
📅 תאריך: {current_date}

💼 מה אני יכולה:
• 🕐 שעה ותאריך מדויקים
• 🌤️ מזג אוויר לכל עיר בישראל
• 📝 עזרה בכתיבה ותכנון
• 🌍 תרגום בין שפות
• 🧠 מענה על שאלות

🎯 פקודות:
/time - שעה נוכחית
/weather - מזג אוויר
/clear - ניקוי היסטוריה
/info - המידע הזה

פשוט דבר איתי טבעית! 😊'''
    
    await context.bot.send_message(chat_id=update.message.chat_id, text=info_text)

def main():
    logging.basicConfig(level=logging.INFO)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    app.add_handler(CommandHandler('time', time_command))
    app.add_handler(CommandHandler('weather', weather_command))
    app.add_handler(CommandHandler('clear', clear_history))
    app.add_handler(CommandHandler('info', info_command))
    
    print('🤖 מאיה הפשוטה והעובדת מוכנה!')
    app.run_polling()

if __name__ == '__main__':
    main()
