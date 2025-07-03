import os
import json
import requests
from datetime import datetime
import pytz
from flask import Flask, request
import telebot
import google.generativeai as genai
import wikipediaapi
import re

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

user_data = {}
chat_sessions = {}

def load_data():
    global user_data
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            user_data = data.get("user_data", {})
    except Exception:
        user_data = {}

def save_data():
    try:
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump({"user_data": user_data}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving data:", e)

def extract_user_info(user_id, text, from_user):
    user_id = str(user_id)
    if user_id not in user_data:
        user_data[user_id] = {}
    updated = False
    if "שם" not in user_data[user_id] and from_user.first_name:
        user_data[user_id]["שם"] = from_user.first_name
        updated = True
    if "קוראים לי" in text:
        try:
            parts = text.split("קוראים לי")
            if len(parts) > 1:
                name = parts[1].strip().split()[0]
                user_data[user_id]["שם"] = name.replace(",", "").replace(".", "")
                updated = True
        except Exception:
            pass
    if updated:
        save_data()
    return updated

# שליפת שם עיר מהמשפט (בעברית/אנגלית)
def extract_city_from_text(text):
    text = text.lower()
    match = re.search(r'(?:בעיר|ב|לעיר)\s*([א-תa-zA-Z\- ]+)', text)
    if match:
        city = match.group(1).strip()
        city = city.replace("עיר", "").strip()
        return city
    return None

# שעה לכל עיר (עברית/אנגלית)
def get_time_for_location(city):
    city = city.strip().lower()
    for tz in pytz.all_timezones:
        tz_parts = tz.split("/")
        if len(tz_parts) > 1 and city in tz_parts[1].replace("_", " ").lower():
            now = datetime.now(pytz.timezone(tz))
            return now.strftime("%H:%M"), tz
    for tz in pytz.all_timezones:
        if city in tz.replace("_", " ").lower():
            now = datetime.now(pytz.timezone(tz))
            return now.strftime("%H:%M"), tz
    # ברירת מחדל: ישראל
    now = datetime.now(pytz.timezone("Asia/Jerusalem"))
    return now.strftime("%H:%M"), "Asia/Jerusalem"

# מזג אוויר - תמיכה בערים בעברית ואנגלית עם גיאוקודינג
def get_weather(city):
    if not WEATHER_API_KEY:
        return "⚠️ לא מוגדר מפתח API למזג אוויר."
    # שלב 1: חפש קואורדינטות של העיר (עברית או אנגלית)
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    geo_params = {"q": city, "limit": 1, "appid": WEATHER_API_KEY}
    try:
        geo_resp = requests.get(geo_url, params=geo_params, timeout=4)
        geo_data = geo_resp.json()
        if not geo_data or not isinstance(geo_data, list) or len(geo_data)==0:
            return f"❗ לא נמצאה עיר בשם {city}. נסה לכתוב באנגלית."
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        # שלב 2: בקשת מזג אוויר לפי קואורדינטות
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric", "lang": "he"}
        resp = requests.get(url, params=params, timeout=4)
        data = resp.json()
        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"מזג האוויר ב{city}: {desc}, {temp}°C"
        else:
            return f"❗ לא נמצאה תחזית לעיר {city}."
    except Exception as e:
        print("Weather error:", e)
        return f"שגיאה בשליפת מזג האוויר לעיר {city}."

# תשובה עובדתית מוויקיפדיה (בעברית/אנגלית)
def get_wikipedia_summary(query, lang="he"):
    wiki = wikipediaapi.Wikipedia(lang)
    page = wiki.page(query)
    if page.exists():
        return page.summary[:700] + f"\n\n(מקור: ויקיפדיה {lang})"
    # fallback לאנגלית
    wiki_en = wikipediaapi.Wikipedia("en")
    page_en = wiki_en.page(query)
    if page_en.exists():
        return page_en.summary[:700] + "\n\n(Source: Wikipedia en)"
    return None

# תשובת בינה מלאכותית
def get_gemini_response(user_id, message_text, from_user):
    try:
        if user_id not in chat_sessions:
            chat_sessions[user_id] = model.start_chat(history=[])
        response = chat_sessions[user_id].send_message(message_text)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        chat_sessions[user_id] = model.start_chat(history=[])
        return "😅 סליחה, קרתה לי שגיאה קטנה. אפשר לנסות שוב?"

@bot.message_handler(commands=["start"])
def start_command(message):
    bot.reply_to(message, "🌟 היי! אני מאיה - עוזרת חכמה, אדיבה ומעודכנת!\nשאל אותי כל מה שתרצה: חדשות, חידושים, מזג אוויר, שעה, ידע כללי או כל דבר בעולם.\nאני כאן בשבילך!")

@bot.message_handler(func=lambda m: not getattr(m.from_user, "is_bot", False))
def handle_message(message):
    try:
        text = message.text.strip()
        user_id = str(message.from_user.id)
        from_user = message.from_user
        extract_user_info(user_id, text, from_user)
        user_info = user_data.get(user_id, {})
        user_name = user_info.get("שם") or from_user.first_name or "חבר"

        # שעה לעיר
        if "שעה" in text:
            city = extract_city_from_text(text)
            if city:
                time_now, tz = get_time_for_location(city)
                if time_now:
                    bot.reply_to(message, f"🕒 {user_name}, השעה עכשיו ב{city}: {time_now}")
                else:
                    bot.reply_to(message, f"❗ לא מצאתי את אזור הזמן של העיר {city}.")
            else:
                now = datetime.now(pytz.timezone("Asia/Jerusalem"))
                bot.reply_to(message, f"🕒 {user_name}, השעה עכשיו בישראל: {now.strftime('%H:%M')}")
            return

        # מזג אוויר לעיר
        if "טמפרטורה" in text or "מזג אוויר" in text:
            city = extract_city_from_text(text)
            if not city:
                city = "תל אביב"
            weather = get_weather(city)
            bot.reply_to(message, weather)
            return

        # ידע כללי - קודם ויקיפדיה!
        if text.startswith("מי זה") or text.startswith("מה זה") or text.startswith("מי זאת") or text.startswith("מהי"):
            query = text.replace("מי זה", "").replace("מה זה", "").replace("מי זאת", "").replace("מהי", "").strip()
            answer = get_wikipedia_summary(query)
            if answer:
                bot.reply_to(message, answer)
                return

        # תשובת בינה מלאכותית
        bot.send_chat_action(message.chat.id, "typing")
        response_text = get_gemini_response(user_id, text, from_user)
        bot.reply_to(message, response_text)
    except Exception as e:
        print(f"Error in handle_message: {e}")
        bot.reply_to(message, "אירעה שגיאה. נסה שוב.")

@app.route("/", methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return "", 500

@app.route("/", methods=["GET"])
def health():
    return "Maya Bot is running! 🤖", 200

def main():
    print("Maya starting...")
    load_data()
    try:
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"Webhook set to: {WEBHOOK_URL}")
    except Exception as e:
        print(f"Webhook setup error: {e}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    main()
