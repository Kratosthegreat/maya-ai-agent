import os
import json
import requests
from datetime import datetime
import pytz
from flask import Flask, request
import telebot
import google.generativeai as genai
import wikipediaapi

# --- הגדרת משתני סביבה נדרשים ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")  # OpenWeatherMap
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
SPORTS_API_KEY = os.environ.get("SPORTS_API_KEY", "")
TICKETMASTER_API_KEY = os.environ.get("TICKETMASTER_API_KEY", "")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

user_data = {}
chat_sessions = {}

CITY_TIMEZONES = {
    "ישראל": "Asia/Jerusalem",
    "תל אביב": "Asia/Jerusalem",
    "חיפה": "Asia/Jerusalem",
    "ירושלים": "Asia/Jerusalem",
    "ניו יורק": "America/New_York",
    "לונדון": "Europe/London",
    "ארגנטינה": "America/Argentina/Buenos_Aires",
    "בואנוס איירס": "America/Argentina/Buenos_Aires",
    "פאריס": "Europe/Paris",
    "ברלין": "Europe/Berlin",
    "סידני": "Australia/Sydney",
    "טוקיו": "Asia/Tokyo",
    "ברצלונה": "Europe/Madrid",
    "ברזיל": "America/Sao_Paulo",
    "מיאמי": "America/New_York",
}

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
    if "שם" not in user_data[user_id]:
        if from_user.first_name:
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
    if any(word in text for word in ["עובד ב", "עובדת ב", "עבודה ב"]):
        user_data[user_id]["עבודה"] = text[:100]
        updated = True
    if updated:
        save_data()
    return updated

def get_time_for_location(location):
    tz_str = CITY_TIMEZONES.get(location)
    if tz_str:
        now = datetime.now(pytz.timezone(tz_str))
        return now.strftime("%H:%M")
    return None

def extract_location_from_text(text):
    text = text.lower()
    for city in CITY_TIMEZONES.keys():
        if city in text:
            return city
    return None

def handle_time_query(text, user_name):
    location = extract_location_from_text(text)
    if location:
        time_now = get_time_for_location(location)
        if time_now:
            return f"🕒 {user_name}, השעה עכשיו ב{location}: {time_now}"
        else:
            return f"לא מצאתי אזור זמן לעיר/מדינה '{location}'."
    time_now = get_time_for_location("ישראל")
    return f"🕒 {user_name}, השעה עכשיו בישראל: {time_now}"

def get_weather(city="תל אביב"):
    if not WEATHER_API_KEY:
        return None
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": "he"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("main"):
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"מזג האוויר ב{city}: {desc}, {temp}°C"
    except Exception as e:
        print("Weather error:", e)
    return None

def get_latest_news(query="ישראל", category=None, language="he"):
    if not NEWS_API_KEY:
        return None
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NEWS_API_KEY,
        "q": query,
        "language": language,
        "country": "il",
        "pageSize": 3
    }
    if category:
        params["category"] = category
    try:
        resp = requests.get(url, params=params, timeout=4)
        data = resp.json()
        if data.get("status") == "ok" and data.get("articles"):
            results = []
            for art in data["articles"]:
                results.append(f"*{art['title']}*\n{art.get('description','')}\n{art['url']}\n")
            return "\n\n".join(results)
        return None
    except Exception as e:
        print("NEWS error:", e)
        return None

def get_technology_news():
    return get_latest_news(category="technology")

def get_latest_sports(team=None, sport="soccer", country="Israel"):
    if not SPORTS_API_KEY:
        return None
    try:
        if team:
            url = f"https://www.thesportsdb.com/api/v1/json/{SPORTS_API_KEY}/searchteams.php"
            resp = requests.get(url, params={"t": team}, timeout=4)
            data = resp.json()
            if data.get("teams"):
                t = data["teams"][0]
                return f"קבוצת {t['strTeam']} ({t['strCountry']}): {t.get('strDescriptionIL', t.get('strDescriptionEN','אין מידע'))[:200]}"
        url = f"https://www.thesportsdb.com/api/v1/json/{SPORTS_API_KEY}/eventsday.php"
        params = {"d": "today", "s": sport, "c": country}
        resp = requests.get(url, params=params, timeout=4)
        data = resp.json()
        if data.get("events"):
            e = data["events"][0]
            return f"משחק: {e['strEvent']} ({e['dateEvent']})\nתוצאה: {e.get('intHomeScore')}:{e.get('intAwayScore')} ({e['strHomeTeam']} נגד {e['strAwayTeam']})"
        return None
    except Exception as e:
        print("SPORTS error:", e)
        return None

def get_culture_events(city="תל אביב"):
    if not TICKETMASTER_API_KEY:
        return None
    url = "https://app.ticketmaster.com/discovery/v2/events"
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "locale": "*",
        "city": city,
        "countryCode": "IL",
        "size": 2,
        "sort": "date,asc"
    }
    try:
        resp = requests.get(url, params=params, timeout=4)
        data = resp.json()
        events = data.get("_embedded", {}).get("events", [])
        if not events:
            return None
        res = []
        for event in events:
            res.append(f"{event['name']} - {event['dates']['start']['localDate']}\n{event['url']}")
        return "\n\n".join(res)
    except Exception as e:
        print("TICKETMASTER error:", e)
        return None

def get_wikipedia_summary(query, lang="he"):
    wiki = wikipediaapi.Wikipedia(lang)
    page = wiki.page(query)
    if page.exists():
        return page.summary[:650] + "..." if len(page.summary) > 650 else page.summary
    return None

def google_search(query):
    if not SERPAPI_KEY:
        return None
    url = f"https://serpapi.com/search"
    params = {"q": query, "api_key": SERPAPI_KEY, "hl": "he"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        results = data.get("organic_results", [])
        if results:
            top = results[0]
            return f"{top.get('title', '')}\n{top.get('snippet', '')}\n{top.get('link', '')}"
    except Exception as e:
        print("Google Search error:", e)
    return None

def get_global_knowledge(query, user_name):
    wiki = get_wikipedia_summary(query)
    if wiki:
        return f"📚 {user_name}, הנה מה שמצאתי בויקיפדיה:\n{wiki}"
    google = google_search(query)
    if google:
        return f"🔎 {user_name}, הנה תוצאה מגוגל:\n{google}"
    return None

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
    bot.reply_to(message, """🌟 היי! אני מאיה - עוזרת חכמה, אדיבה ומעודכנת!
שאל אותי כל מה שתרצה: חדשות, חידושים, מזג אוויר, ספורט, תרבות, ידע כללי או כל דבר בעולם.
אני כאן בשבילך!""")

@bot.message_handler(func=lambda m: not getattr(m.from_user, "is_bot", False))
def handle_message(message):
    text = message.text
    user_id = str(message.from_user.id)
    from_user = message.from_user
    extract_user_info(user_id, text, from_user)
    user_info = user_data.get(user_id, {})
    user_name = user_info.get("שם") or from_user.first_name or "חבר"

    # --- זמן/שעון לכל עיר בעולם ---
    if any(phrase in text for phrase in ["מה השעה", "איזה שעה", "כמה השעה"]):
        bot.reply_to(message, handle_time_query(text, user_name))
        return

    # --- מזג אוויר ---
    if "מזג אוויר" in text or "טמפרטורה" in text:
        city = extract_location_from_text(text) or "תל אביב"
        weather = get_weather(city)
        if weather:
            bot.reply_to(message, weather)
        else:
            bot.reply_to(message, f"מצטערת, לא מצאתי תחזית לעיר {city}.")
        return

    # --- חדשות כלליות ---
    if "חדשות" in text or "אקטואליה" in text:
        news = get_latest_news()
        if news:
            bot.reply_to(message, f"📰 הנה החדשות הכי עדכניות:\n\n{news}")
        else:
            bot.reply_to(message, "מצטערת, לא הצלחתי להביא חדשות כרגע.")
        return

    # --- טכנולוגיה / חידושים ---
    if "חידוש" in text or "טכנולוג" in text or "חדשנות" in text:
        tech_news = get_technology_news()
        if tech_news:
            bot.reply_to(message, f"🤖 הנה החדשות הטכנולוגיות הכי עדכניות:\n\n{tech_news}")
        else:
            bot.reply_to(message, "מצטערת, לא הצלחתי להביא חדשות טכנולוגיה כרגע.")
        return

    # --- ספורט ---
    if "ספורט" in text or "תוצאה" in text or "משחק" in text:
        sports = get_latest_sports()
        if sports:
            bot.reply_to(message, f"⚽ עדכון ספורט אחרון:\n{sports}")
        else:
            bot.reply_to(message, "לא מצאתי תוצאות ספורט כרגע, נסה שוב מאוחר יותר.")
        return

    # --- פנאי/תרבות/אירועים ---
    if "הופעה" in text or "אירוע" in text or "תרבות" in text or "פנאי" in text:
        city = extract_location_from_text(text) or "תל אביב"
        culture = get_culture_events(city=city)
        if culture:
            bot.reply_to(message, f"🎭 אירועי תרבות ופנאי ב{city}:\n{culture}")
        else:
            bot.reply_to(message, f"לא מצאתי כרגע אירועים ב{city}.")
        return

    # --- ידע כללי מהעולם (ויקיפדיה/גוגל) ---
    global_answer = get_global_knowledge(text, user_name)
    if global_answer:
        bot.reply_to(message, global_answer)
        return

    # --- תשובת בינה מלאכותית (Gemini/OpenAI) ---
    bot.send_chat_action(message.chat.id, "typing")
    response_text = get_gemini_response(user_id, text, from_user)
    bot.reply_to(message, response_text)

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
    print("Maya SuperBot starting...")
    load_data()
    try:
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
    except Exception as e:
        print(f"Webhook setup error: {e}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()
