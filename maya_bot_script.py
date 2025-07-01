import logging
import random
import asyncio
import httpx
import json
import time
import os
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import pickle

# הגדרות
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7876544988:AAFZUHIzHOqyzpJ5TIec2hJFtdiawc4JMF4")
GEMINI_API_KEY = "AIzaSyBoIvgf3WlDQj1gDfGySUOi_JXqR-8GdcM"

# Google Calendar הגדרות
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'  # תצטרך להעלות את זה
TOKEN_FILE = 'token.pickle'

# הגדרת Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# היסטוריית שיחה
chat_sessions = {}

# Google Calendar Service
calendar_service = None

def get_current_time_israel():
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(israel_tz)
    return now.strftime("%H:%M:%S"), now.strftime("%A, %d %B %Y"), now

async def get_weather_data(city="תל אביב"):
    """מביא נתוני מזג אוויר לעיר מבוקשת"""
    try:
        # קואורדינטות של ערים בישראל
        city_coords = {
            "תל אביב": (32.0853, 34.7818),
            "ירושלים": (31.7683, 35.2137),
            "חיפה": (32.7940, 34.9896),
            "באר שבע": (31.2518, 34.7915),
            "עפולה": (32.6098, 35.2897),
            "נתניה": (32.3215, 34.8532),
            "אשדוד": (31.7940, 34.6436),
            "פתח תקווה": (32.0878, 34.8878),
            "ראשון לציון": (31.9730, 34.7925),
            "חולון": (32.0178, 34.7925)
        }
        
        # מציאת העיר המתאימה
        city_lower = city.lower()
        matched_city = None
        matched_coords = None
        
        for city_name, coords in city_coords.items():
            if city_lower in city_name.lower() or city_name.lower() in city_lower:
                matched_city = city_name
                matched_coords = coords
                break
        
        # אם לא מצאנו, נשתמש בתל אביב
        if not matched_coords:
            matched_city = "תל אביב"
            matched_coords = city_coords["תל אביב"]
        
        lat, lon = matched_coords
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Jerusalem"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                current = data["current_weather"]
                
                temp = current["temperature"]
                windspeed = current["windspeed"]
                
                weather_codes = {
                    0: "שמיים בהירים", 1: "בהיר ברובו", 2: "חלקית מעונן",
                    3: "מעונן", 45: "ערפל", 48: "ערפל קפוא",
                    51: "טפטוף קל", 53: "טפטוף בינוני", 55: "טפטוף חזק",
                    61: "גשם קל", 63: "גשם בינוני", 65: "גשם חזק",
                    80: "ממטרים קלים", 81: "ממטרים חזקים", 95: "סופת רעמים"
                }
                
                description = weather_codes.get(current["weathercode"], "מזג אוויר משתנה")
                
                return {
                    "temp": temp,
                    "windspeed": windspeed,
                    "description": description,
                    "city": matched_city
                }
    except Exception as e:
        logging.error(f"שגיאה בקבלת מזג אוויר: {e}")
    return None

def authenticate_google_calendar():
    """אימות Google Calendar"""
    global calendar_service
    creds = None
    
    # טוען credentials קיימים
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # אם אין credentials תקפים
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # צריך אימות ראשוני
            if os.path.exists(CREDENTIALS_FILE):
                flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                print(f"לך לקישור הזה לאימות: {auth_url}")
                print("העתק את הקוד ממסך האישור ותכניס אותו כאן:")
                code = input("קוד אישור: ")
                
                flow.fetch_token(code=code)
                creds = flow.credentials
            else:
                print("אין קובץ credentials.json")
                return None
    
    # שמירת הcredentials
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)
    
    calendar_service = build('calendar', 'v3', credentials=creds)
    return calendar_service

async def create_calendar_event(summary, start_datetime, end_datetime, attendee_email=None):
    """יוצר אירוע חדש ביומן"""
    try:
        if not calendar_service:
            return "אני לא מחוברת ליומן כרגע"
        
        # הכנת האירוע
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Asia/Jerusalem',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Asia/Jerusalem',
            },
        }
        
        # הוספת משתתף אם צוין
        if attendee_email:
            event['attendees'] = [{'email': attendee_email}]
        
        # יצירת האירוע
        created_event = calendar_service.events().insert(calendarId='primary', body=event).execute()
        
        return f"נקבע! ישיבה עם {attendee_email or 'ללא משתתפים'} ב{start_datetime.strftime('%d/%m/%Y בשעה %H:%M')}"
        
    except Exception as e:
        logging.error(f"שגיאה ביצירת אירוע: {e}")
        return "היתה בעיה ביצירת האירוע ביומן"

async def get_upcoming_events(max_results=10):
    """מביא אירועים קרובים"""
    try:
        if not calendar_service:
            return "אני לא מחוברת ליומן כרגע"
        
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = calendar_service.events().list(
            calendarId='primary', timeMin=now, maxResults=max_results,
            singleEvents=True, orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "אין אירועים קרובים ביומן"
        
        events_text = "האירועים הקרובים:\n\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'ללא כותרת')
            events_text += f"• {summary} - {start}\n"
        
        return events_text
        
    except Exception as e:
        logging.error(f"שגיאה בקבלת אירועים: {e}")
        return "היתה בעיה בקבלת האירועים מהיומן"

def parse_meeting_request(message):
    """מנתח בקשה לקביעת פגישה"""
    import re
    
    # חיפוש שעה (8:00, 09:30, וכו')
    time_match = re.search(r'(\d{1,2}):?(\d{0,2})', message)
    
    # חיפוש אימייל או שם
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
    name_match = re.search(r'עם (.+?)(?:\s|$)', message)
    
    # חיפוש יום (מחר, היום, תאריך ספציפי)
    day_patterns = {
        'מחר': 1,
        'היום': 0,
        'מחרתיים': 2,
        'ביום ראשון': None,
        'ביום שני': None,
    }
    
    target_day = 1  # ברירת מחדל - מחר
    for day_word, day_offset in day_patterns.items():
        if day_word in message and day_offset is not None:
            target_day = day_offset
            break
    
    return {
        'time_match': time_match,
        'email': email_match.group() if email_match else None,
        'name': name_match.group(1) if name_match else None,
        'day_offset': target_day
    }

def create_enhanced_system_prompt():
    current_time, current_date, current_dt = get_current_time_israel()
    
    return f"""את מאיה, המזכירה האישית של דוד. דברי איתו טבעית וחכמה.

השעה עכשיו: {current_time}, {current_date}

תהיי חכמה ומבינה:
- אם דוד שואל על מזג אוויר בעיר מסוימת - תני לו בדיוק מה שהוא ביקש
- אם הוא לא מבין למה נתת לו מידע על עיר אחרת - תסבירי ותתקני
- אל תגידי "אני לא מבינה" - נסי להבין מההקשר
- תהיי ישירה ומועילה

דוגמה: אם הוא שואל "למה ת״א??" אחרי שנתת מזג אוויר לתל אביב כשהוא ביקש עפולה - תגידי משהו כמו:
"אה סליחה! אתה ביקשת מזג אוויר לעפולה ולא לתל אביב. בוא אבדוק לך את עפולה..."

תהיי מאיה החכמה שמבינה ומתקנת טעויות!"""

def create_chat_session():
    chat = model.start_chat(history=[])
    system_prompt = create_enhanced_system_prompt()
    chat.send_message(system_prompt)
    return chat

quick_replies = [
    "בוקר טוב דוד! מה בתוכנית היום? 📅",
    "היי! רוצה שאבדוק מה יש לך ביומן?",
    "שלום! איך אפשר לעזור? לקבוע פגישה?",
    "אהלן! יש לי גישה ליומן שלך עכשיו! 🗓️",
    "היי! מה נקבע היום?",
]

def is_quick_message(msg):
    return msg.lower().strip() in ["היי", "היי מאיה", "מאיה", "מה קורה", "את פה", "נו", "שלום", "מה המצב", "בוקר טוב"]

async def respond(update, context):
    user_message = update.message.text.strip()
    chat_id = update.message.chat_id

    if is_quick_message(user_message):
        current_time, current_date, _ = get_current_time_israel()
        reply = random.choice(quick_replies)
        reply += f"\n\n🕐 השעה: {current_time}\n📅 {current_date}"
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # בדיקה אם זו בקשה לקביעת פגישה
    if any(word in user_message.lower() for word in ["קבע", "פגישה", "ישיבה", "מפגש"]):
        parsed = parse_meeting_request(user_message)
        
        if parsed['time_match']:
            try:
                # חישוב התאריך והשעה
                _, _, current_dt = get_current_time_israel()
                target_date = current_dt + timedelta(days=parsed['day_offset'])
                
                hour = int(parsed['time_match'].group(1))
                minute = int(parsed['time_match'].group(2)) if parsed['time_match'].group(2) else 0
                
                start_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                end_time = start_time + timedelta(hours=1)  # פגישה של שעה
                
                # יצירת הפגישה
                attendee = parsed['email'] or parsed['name']
                summary = f"פגישה עם {attendee}" if attendee else "פגישה"
                
                result = await create_calendar_event(summary, start_time, end_time, parsed['email'])
                await context.bot.send_message(chat_id=chat_id, text=f"✅ {result}")
                return
                
            except Exception as e:
                await context.bot.send_message(chat_id=chat_id, text="היתה בעיה בקביעת הפגישה. תוכל לנסח אחרת?")
                return

    # בדיקה אם זו בקשה לראות יומן
    if any(word in user_message.lower() for word in ["יומן", "לוח", "אירועים", "פגישות שלי"]):
        events = await get_upcoming_events()
        await context.bot.send_message(chat_id=chat_id, text=events)
        return

    # שעה
    if any(word in user_message.lower() for word in ["שעה", "זמן", "מתי", "איזה שעה"]):
        current_time, current_date, _ = get_current_time_israel()
        reply = f"🕐 השעה עכשיו: {current_time}\n📅 התאריך: {current_date}"
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return
    
    # מזג אוויר
    if any(word in user_message.lower() for word in ["מזג אוויר", "טמפרטורה", "חם", "קר", "גשם", "מזג"]):
        # חיפוש עיר בהודעה
        cities = ["עפולה", "תל אביב", "ירושלים", "חיפה", "באר שבע", "נתניה", "אשדוד", "פתח תקווה", "ראשון לציון", "חולון"]
        requested_city = "תל אביב"  # ברירת מחדל
        
        for city in cities:
            if city in user_message:
                requested_city = city
                break
        
        weather_data = await get_weather_data(requested_city)
        if weather_data:
            reply = f"🌤️ מזג האוויר ב{weather_data['city']}:\n🌡️ {weather_data['temp']}°C\n💨 רוח: {weather_data['windspeed']} קמ\"ש\n☁️ {weather_data['description']}"
        else:
            reply = f"לא הצלחתי לקבל נתוני מזג אוויר עבור {requested_city} כרגע"
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    # תגובה כללית עם Gemini
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = create_chat_session()

    try:
        current_time, current_date, _ = get_current_time_israel()
        
        enhanced_message = f"""דוד אמר: "{user_message}"

מידע עדכני:
- שעה: {current_time}
- תאריך: {current_date}
- יש לי גישה ליומן Google שלו

תני תשובה מועילה וטבעית."""
        
        chat_session = chat_sessions[chat_id]
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: chat_session.send_message(enhanced_message)
        )
        
        reply = response.text
        await context.bot.send_message(chat_id=chat_id, text=reply)

    except Exception as e:
        logging.error(f"שגיאה בתגובה: {e}")
        await context.bot.send_message(chat_id=chat_id, text="יש לי תקלה קטנה... תנסה שוב?")

async def calendar_command(update, context):
    """פקודה לראות יומן"""
    events = await get_upcoming_events()
    await context.bot.send_message(chat_id=update.message.chat_id, text=events)

async def time_command(update, context):
    current_time, current_date, _ = get_current_time_israel()
    reply = f"🕐 השעה: {current_time}\n📅 {current_date}"
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def weather_command(update, context):
    weather_data = await get_weather_data()
    if weather_data:
        reply = f"🌤️ מזג האוויר בתל אביב:\n🌡️ {weather_data['temp']}°C\n💨 רוח: {weather_data['windspeed']} קמ\"ש\n☁️ {weather_data['description']}"
    else:
        reply = "לא ניתן לקבל נתוני מזג אוויר כרגע"
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

def main():
    logging.basicConfig(level=logging.INFO)
    
    # אימות Google Calendar
    print("מתחבר ל-Google Calendar...")
    auth_result = authenticate_google_calendar()
    if auth_result:
        print("✅ מחובר ל-Google Calendar!")
    else:
        print("❌ בעיה בחיבור ל-Google Calendar")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    app.add_handler(CommandHandler("calendar", calendar_command))
    app.add_handler(CommandHandler("time", time_command))
    app.add_handler(CommandHandler("weather", weather_command))
    
    print("🤖 מאיה עם Google Calendar מוכנה!")
    app.run_polling()

if __name__ == "__main__":
    main()
