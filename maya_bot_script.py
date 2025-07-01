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

# הגדרות
TELEGRAM_TOKEN = "7876544988:AAGbjUJ6PNh1JH_HYzZ6MQpMoZNAWMYrssE"
GEMINI_API_KEY = "AIzaSyBoIvgf3WlDQj1gDfGySUOi_JXqR-8GdcM"

# הגדרת Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# היסטוריית שיחה
chat_sessions = {}

def get_current_time_israel():
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(israel_tz)
    return now.strftime("%H:%M:%S"), now.strftime("%A, %d %B %Y")

async def get_weather_data():
    try:
        lat, lon = 32.0853, 34.7818
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Jerusalem"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                current = data["current_weather"]
                
                temp = current["temperature"]
                windspeed = current["windspeed"]
                
                weather_codes = {
                    0: "שמיים בהירים",
                    1: "בהיר ברובו", 
                    2: "חלקית מעונן",
                    3: "מעונן",
                    45: "ערפל",
                    48: "ערפל קפוא",
                    51: "טפטוף קל",
                    53: "טפטוף בינוני", 
                    55: "טפטוף חזק",
                    61: "גשם קל",
                    63: "גשם בינוני",
                    65: "גשם חזק",
                    80: "ממטרים קלים",
                    81: "ממטרים חזקים",
                    95: "סופת רעמים"
                }
                
                description = weather_codes.get(current["weathercode"], "מזג אוויר משתנה")
                
                return {
                    "temp": temp,
                    "windspeed": windspeed,
                    "description": description,
                    "city": "תל אביב"
                }
    except Exception as e:
        logging.error(f"שגיאה בקבלת מזג אוויר: {e}")
    return None

def check_business_hours():
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(israel_tz)
    hour = now.hour
    weekday = now.weekday()
    
    if weekday < 5 and 8 <= hour <= 18:
        return "שעות עבודה"
    elif weekday == 4 and hour >= 15:
        return "כמעט סוף השבוע"
    elif weekday >= 5:
        return "סוף שבוע"
    else:
        return "מחוץ לשעות עבודה"

def create_enhanced_system_prompt():
    current_time, current_date = get_current_time_israel()
    business_status = check_business_hours()
    
    return f"""את מאיה, המזכירה האישית והמקצועית של דוד. את לא רק צ'אטבוט - את מזכירה אמיתית עם גישה למידע עדכני.

המידע שיש לך:
- השעה הנוכחת: {current_time}
- התאריך: {current_date}
- סטטוס עבודה: {business_status}
- מיקום: תל אביב, ישראל

היכולות שלך כמזכירה:
✅ לספק שעה ותאריך מדויקים
✅ לבדוק מזג אוויר עדכני
✅ לעזור עם תזמון פגישות
✅ לתת עדכונים על מצב עבודה
✅ לעזור עם משימות יומיות
✅ לזכור דברים חשובים

האישיות שלך:
- מקצועית אבל חמה
- יעילה ומדויקת
- יזומה בהצעת עזרה
- זוכרת פרטים חשובים
- מדברת בעברית טבעית

כשדוד שואל על שעה, מזג אוויר, או מידע עדכני - תני לו תשובה מדויקת ומועילת.
אל תפני אותו לבדוק במקומות אחרים - את המזכירה שלו!"""

def create_chat_session():
    chat = model.start_chat(history=[])
    system_prompt = create_enhanced_system_prompt()
    chat.send_message(system_prompt)
    return chat

quick_replies = [
    "בוקר טוב דוד! איך אפשר לעזור היום? 😊",
    "היי! מה בתוכנית היום?",
    "שלום דוד! יש לי עדכונים בשבילך או שאתה צריך משהו?",
    "אהלן! איך אני יכולה לעזור לך להיות יותר יעיל היום?",
    "היי! רוצה שאבדוק לך משהו? מזג אוויר? פגישות?",
    "בוקר טוב! מה החשוב ביותר שעליי לדעת היום?"
]

def is_quick_message(msg):
    return msg.lower().strip() in ["היי", "היי מאיה", "מאיה", "מה קורה", "את פה", "נו", "שלום", "מה המצב", "בוקר טוב"]

async def respond(update, context):
    user_message = update.message.text.strip()
    chat_id = update.message.chat_id

    if is_quick_message(user_message):
        current_time, current_date = get_current_time_israel()
        business_status = check_business_hours()
        
        reply = random.choice(quick_replies)
        reply += f"\n\n🕐 השעה: {current_time}\n📅 {current_date}\n💼 {business_status}"
        
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    if any(word in user_message.lower() for word in ["שעה", "זמן", "מתי", "איזה שעה"]):
        current_time, current_date = get_current_time_israel()
        reply = f"🕐 השעה עכשיו: {current_time}\n📅 התאריך: {current_date}"
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return
    
    if any(word in user_message.lower() for word in ["מזג אוויר", "טמפרטורה", "חם", "קר", "גשם", "מזג"]):
        weather_data = await get_weather_data()
        if weather_data:
            reply = f"🌤️ מזג האוויר בתל אביב:\n"
            reply += f"🌡️ טמפרטורה: {weather_data['temp']}°C\n"
            reply += f"💨 רוח: {weather_data['windspeed']} קמ\"ש\n"
            reply += f"☁️ מצב: {weather_data['description']}"
        else:
            reply = "😅 מצטערת, יש לי בעיה לקבל נתוני מזג אוויר כרגע. תוכל לבדוק באפליקציית מזג האוויר?"
        
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = create_chat_session()

    try:
        current_time, current_date = get_current_time_israel()
        enhanced_message = f"""המידע העדכני:
- שעה: {current_time}
- תאריך: {current_date}
- מיקום: תל אביב

שאלת המשתמש: {user_message}

תני תשובה מועילה ומדויקת כמזכירה מקצועית."""
        
        chat_session = chat_sessions[chat_id]
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: chat_session.send_message(enhanced_message)
        )
        
        reply = response.text
        
        if len(reply) > 4096:
            for i in range(0, len(reply), 4096):
                chunk = reply[i:i+4096]
                await context.bot.send_message(chat_id=chat_id, text=chunk)
        else:
            await context.bot.send_message(chat_id=chat_id, text=reply)

    except Exception as e:
        logging.error(f"שגיאה בתגובה: {e}")
        error_reply = "😅 יש לי בעיה טכנית קטנה כרגע. תוכל לנסות שוב בעוד רגע?"
        await context.bot.send_message(chat_id=chat_id, text=error_reply)

async def time_command(update, context):
    current_time, current_date = get_current_time_israel()
    business_status = check_business_hours()
    
    reply = f"🕐 השעה: {current_time}\n📅 {current_date}\n💼 {business_status}"
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def weather_command(update, context):
    weather_data = await get_weather_data()
    if weather_data:
        reply = f"🌤️ מזג האוויר בתל אביב:\n"
        reply += f"🌡️ {weather_data['temp']}°C\n"
        reply += f"💨 רוח: {weather_data['windspeed']} קמ\"ש\n"
        reply += f"☁️ {weather_data['description']}"
    else:
        reply = "😅 לא ניתן לקבל נתוני מזג אוויר כרגע"
    
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def clear_history(update, context):
    chat_id = update.message.chat_id
    chat_sessions[chat_id] = create_chat_session()
    
    clear_messages = [
        "נוקה! התחלנו שיחה חדשה 🧹",
        "מחקתי הכל! מה נעשה עכשיו? ✨",
        "היסטוריה נמחקה! איך אפשר לעזור? 🎉"
    ]
    reply = random.choice(clear_messages)
    await context.bot.send_message(chat_id=chat_id, text=reply)

async def info_command(update, context):
    current_time, current_date = get_current_time_israel()
    
    info_text = f"""🤖 מאיה - המזכירה החכמה שלך

🕐 זמן עדכני: {current_time}
📅 תאריך: {current_date}

💼 מה אני יכולה לעזור:
• 🕐 לתת שעה ותאריך מדויקים
• 🌤️ לבדוק מזג אוויר
• 📅 לעזור עם תזמון ותכנון
• 📝 לכתוב ולערוך טקסטים
• 🌍 לתרגם בין שפות
• 🧠 לענות על שאלות מורכבות

🎯 פקודות מהירות:
/time - שעה נוכחית
/weather - מזג אוויר
/clear - ניקוי היסטוריה
/info - המידע הזה

פשוט דבר איתי כמו עם מזכירה אמיתית! 😊"""
    
    await context.bot.send_message(chat_id=update.message.chat_id, text=info_text)

def main():
    logging.basicConfig(level=logging.INFO)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    app.add_handler(CommandHandler("time", time_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("info", info_command))
    
    print("🤖 מאיה המזכירה החכמה מוכנה!")
    app.run_polling()

if __name__ == "__main__":
    main()
