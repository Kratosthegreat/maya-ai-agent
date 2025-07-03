import os
import json
import threading
from datetime import datetime, timedelta
import pytz
import telebot
import google.generativeai as genai
from langdetect import detect
import dateparser

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_data = {}
tasks = {}
contacts = {}

def save_data():
    try:
        with open("data.json", "w") as f:
            json.dump({"user_data": user_data, "tasks": tasks, "contacts": contacts}, f)
    except Exception as e:
        print("Error saving data:", e)

def load_data():
    global user_data, tasks, contacts
    try:
        with open("data.json", "r") as f:
            data = json.load(f)
            user_data = data.get("user_data", {})
            tasks = data.get("tasks", {})
            contacts = data.get("contacts", {})
    except Exception:
        user_data = {}
        tasks = {}
        contacts = {}

def detect_language(text):
    try:
        return detect(text)
    except Exception:
        return "he"

def parse_datetime_from_text(text, lang="he"):
    # תומך בעברית, אנגלית ועוד
    settings = {'TIMEZONE': 'Asia/Jerusalem', 'RETURN_AS_TIMEZONE_AWARE': True}
    if lang == "he":
        return dateparser.parse(text, languages=["he"], settings=settings)
    return dateparser.parse(text, settings=settings)

def extract_entities_llm(text, user_id=None):
    """
    מבקש מה-LLM להוציא ישויות מהמשפט: משימה, שמות, תאריך, פעולה
    """
    prompt = (
        "נתון המשפט הבא של משתמש:\n"
        f"\"{text}\"\n"
        "הוצא בפורמט JSON את:\n"
        "- intent: מה המשתמש רוצה (למשל: תזכורת, פגישה, שליחת הודעה)\n"
        "- task: תיאור המשימה או ההודעה\n"
        "- contact: שם איש קשר (אם קיים)\n"
        "- datetime: מתי (אם קיים, בפורמט ISO)\n"
        "- language: זיהוי שפה (he/en/...)\n"
        "ענה רק ב-JSON."
    )
    try:
        response = model.generate_content(prompt)
        import re, json
        json_text = re.search(r"{.*}", response.text, re.DOTALL)
        if json_text:
            return json.loads(json_text.group(0))
    except Exception as e:
        print("LLM entity extraction error:", e)
    return {}

def add_task(user_id, task, dt, contact=None):
    user_tasks = tasks.setdefault(str(user_id), [])
    user_tasks.append({"task": task, "datetime": dt, "contact": contact, "status": "pending"})
    save_data()

def add_contact(user_id, name):
    user_contacts = contacts.setdefault(str(user_id), {})
    user_contacts[name] = {}
    save_data()

def schedule_reminder(user_id, text, remind_time):
    def reminder_job():
        now = datetime.now(pytz.timezone('Asia/Jerusalem'))
        seconds = (remind_time - now).total_seconds()
        if seconds > 0:
            threading.Timer(seconds, lambda: bot.send_message(user_id, f"תזכורת: {text}")).start()
    reminder_job()

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    lang = detect_language(message.text)
    entities = extract_entities_llm(message.text, user_id=message.from_user.id)
    intent = entities.get("intent")
    task = entities.get("task")
    contact = entities.get("contact")
    dt_text = entities.get("datetime")
    detected_lang = entities.get("language", lang)
    dt = None
    if dt_text:
        try:
            dt = dateparser.parse(dt_text)
        except Exception:
            dt = parse_datetime_from_text(dt_text, detected_lang)
    else:
        dt = parse_datetime_from_text(message.text, detected_lang)

    reply = ""
    if intent in ["reminder", "תזכורת"]:
        add_task(message.from_user.id, task, dt.isoformat() if dt else None, contact)
        if dt and dt > datetime.now(pytz.timezone('Asia/Jerusalem')):
            schedule_reminder(message.chat.id, task, dt)
        if contact:
            add_contact(message.from_user.id, contact)
        reply = f"הוספתי תזכורת: {task} ל-{contact or 'עצמך'} ב-{dt.strftime('%d/%m/%Y %H:%M') if dt else 'לא צויין זמן'}"
    elif intent in ["meeting", "פגישה"]:
        add_task(message.from_user.id, task, dt.isoformat() if dt else None, contact)
        if contact:
            add_contact(message.from_user.id, contact)
        reply = f"קבעתי פגישה: {task} עם {contact} ל-{dt.strftime('%d/%m/%Y %H:%M') if dt else 'לא צויין זמן'}"
    elif intent in ["message", "שליחת הודעה"]:
        if contact:
            add_contact(message.from_user.id, contact)
            reply = f"הודעה נשלחה ל-{contact}: {task}"
        else:
            reply = "אנא ציין למי לשלוח את ההודעה."
    else:
        # fallback: תשובה חכמה כללית
        reply = f"זיהיתי: {intent or 'לא זוהתה כוונה ברורה'}, משימה: {task}, איש קשר: {contact}, זמן: {dt}"

    bot.reply_to(message, reply)

def main():
    load_data()
    bot.polling()

if __name__ == "__main__":
    main()
