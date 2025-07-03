import os
import json
import logging
import random
import asyncio
import httpx
from datetime import datetime
import pytz
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler
import google.generativeai as genai

# --- SETTINGS ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Secure token handling
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Secure API key handling
USER_MEMORY_FILE = "maya_memory.json"  # Persistent memory file for user data

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- GLOBAL VARIABLES ---
user_memory = {}
chat_sessions = {}

# Flask app for webhook
app = Flask(__name__)

# --- MEMORY MANAGEMENT ---
def load_memory():
    """Loads persistent memory from a file."""
    global user_memory
    try:
        if os.path.exists(USER_MEMORY_FILE):
            with open(USER_MEMORY_FILE, "r", encoding="utf-8") as f:
                user_memory = json.load(f)
    except Exception as e:
        logging.error(f"Error loading memory: {e}")
        user_memory = {}

def save_memory():
    """Saves user memory to a file."""
    try:
        with open(USER_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(user_memory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving memory: {e}")

load_memory()  # Load memory during startup

# --- TIME FUNCTIONS ---
def get_current_time_israel():
    """Gets the current time and date in Israel."""
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(israel_tz)
    return now.strftime("%H:%M"), now.strftime("%A, %d %B %Y")

# --- WEATHER FUNCTIONS ---
async def get_weather_data(city="תל אביב"):
    """Fetches weather data for a specific city using Open-Meteo."""
    city_coords = {
        "תל אביב": (32.0853, 34.7818),
        "ירושלים": (31.7683, 35.2137),
        "חיפה": (32.7940, 34.9896),
        "באר שבע": (31.2518, 34.7915),
        "עפולה": (32.6098, 35.2897),
        "נתניה": (32.3215, 34.8532)
    }
    try:
        matched_coords = city_coords.get(city, city_coords["תל אביב"])
        lat, lon = matched_coords
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Jerusalem"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                current = data["current_weather"]
                temp = current["temperature"]
                windspeed = current["windspeed"]
                description = current.get("weathercode", "מזג אוויר משתנה")
                return f"🌤️ מזג האוויר ב{city}:\n🌡️ טמפרטורה: {temp}°C\n💨 רוח: {windspeed} קמ\"ש\n☁️ {description}"
    except Exception as e:
        logging.error(f"Weather error: {e}")
        return f"❗ לא הצלחתי לקבל נתוני מזג אוויר עבור {city}"

# --- USER MEMORY MANAGEMENT ---
def update_user_memory(user_id, new_info=None):
    """Updates or initializes user memory."""
    global user_memory
    user_id = str(user_id)
    if user_id not in user_memory:
        user_memory[user_id] = {
            "name": "משתמש",
            "preferences": [],
            "important_info": [],
            "last_seen": datetime.now().isoformat(),
            "conversation_count": 0
        }
    user_data = user_memory[user_id]
    user_data["last_seen"] = datetime.now().isoformat()
    user_data["conversation_count"] += 1
    if new_info and new_info not in user_data["important_info"]:
        user_data["important_info"].append(new_info)
        if len(user_data["important_info"]) > 10:
            user_data["important_info"] = user_data["important_info"][-10:]
    save_memory()

def get_user_context(user_id):
    """Generates context for a user based on memory."""
    user_data = user_memory.get(str(user_id), {})
    context = f"שם: {user_data.get('name', 'משתמש')}\n"
    context += f"מספר שיחות: {user_data.get('conversation_count', 0)}\n"
    if user_data.get("important_info"):
        context += "דברים שאני זוכרת עליך:\n"
        context += "\n".join([f"• {info}" for info in user_data["important_info"][-5:]])
    return context

# --- TELEGRAM BOT FUNCTIONS ---
async def respond(update, context):
    """Handles user messages."""
    user_message = update.message.text.strip()
    chat_id = update.message.chat_id
    user_id = update.effective_user.id

    # Update user memory
    update_user_memory(user_id)

    # Quick response for casual messages
    if user_message.lower() in ["היי", "מה קורה", "מאיה"]:
        current_time, current_date = get_current_time_israel()
        reply = random.choice([
            f"היי! שמחה לראות אותך שוב 😊",
            f"אהלן! איך הולך?",
            f"מה חדש אצלך?"
        ])
        reply += f"\n\n🕐 {current_time} | 📅 {current_date}"
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    # Weather queries
    if any(word in user_message.lower() for word in ["מזג אוויר", "טמפרטורה"]):
        city = next((c for c in ["תל אביב", "ירושלים", "חיפה"] if c in user_message), "תל אביב")
        weather_data = await get_weather_data(city)
        await context.bot.send_message(chat_id=chat_id, text=weather_data)
        return

    # General AI response
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = model.start_chat(history=[])
    enhanced_message = f"דוד אמר: \"{user_message}\"\n{get_user_context(user_id)}"
    chat = chat_sessions[chat_id]
    response = await asyncio.get_event_loop().run_in_executor(None, lambda: chat.send_message(enhanced_message))
    await context.bot.send_message(chat_id=chat_id, text=response.text)

async def memory_command(update, context):
    """Shows what the bot remembers about the user."""
    user_id = update.effective_user.id
    reply = f"🧠 מה שאני זוכרת עליך:\n\n{get_user_context(user_id)}"
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def forget_command(update, context):
    """Clears the user's memory."""
    user_id = update.effective_user.id
    user_id = str(user_id)
    if user_id in user_memory:
        del user_memory[user_id]
        save_memory()
        reply = "שכחתי הכל עליך! נתחיל מחדש 🧹"
    else:
        reply = "ממילא לא זכרתי עליך כלום 😅"
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

async def stats_command(update, context):
    """Displays bot statistics."""
    total_users = len(user_memory)
    total_conversations = sum(data.get("conversation_count", 0) for data in user_memory.values())
    reply = f"📊 סטטיסטיקות:\n👥 משתמשים: {total_users}\n💬 שיחות: {total_conversations}\n🧠 זוכרת הכל!"
    await context.bot.send_message(chat_id=update.message.chat_id, text=reply)

# --- MAIN FUNCTION ---
def main():
    """Starts the bot."""
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("forget", forget_command))
    app.add_handler(CommandHandler("stats", stats_command))
    print("Maya bot is ready!")
    app.run_polling()

if __name__ == "__main__":
    main()