import os
import json
import threading
from datetime import datetime, timedelta
import pytz
import telebot
import google.generativeai as genai
from http.server import HTTPServer, BaseHTTPRequestHandler

# Google Calendar imports
from google.oauth2 import service_account
from googleapiclient.discovery import build

# For language detection/translation
from langdetect import detect
from googletrans import Translator

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")  # The calendar to use for events

if not TELEGRAM_TOKEN or not GEMINI_API_KEY or not GOOGLE_CALENDAR_ID:
    print("Missing tokens or calendar ID")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
bot = telebot.TeleBot(TELEGRAM_TOKEN)
translator = Translator()

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

### 1. Google Calendar Integration ###
def get_calendar_service():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_JSON,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print("Google Calendar error:", e)
        return None

def add_event_to_calendar(title, start_time, end_time=None, description=None):
    service = get_calendar_service()
    if not service:
        return "שגיאה בגישה ליומן גוגל."
    event = {
        'summary': title,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Jerusalem'},
        'end': {'dateTime': (end_time or (start_time + timedelta(hours=1))).isoformat(), 'timeZone': 'Asia/Jerusalem'},
        'description': description or ""
    }
    try:
        event = service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=event).execute()
        return f"אירוע נוסף ליומן: {title} בתאריך {start_time.strftime('%d/%m/%Y %H:%M')}"
    except Exception as e:
        print("Failed to add event:", e)
        return "לא הצלחתי להוסיף את האירוע ליומן."

### 2. תזכורות אוטומטיות (שליחה בזמן אמת) ###
def schedule_reminder(user_id, text, remind_time):
    """
    Schedules a reminder (this is a simple in-memory check, for production use APScheduler or similar)
    """
    def reminder_job():
        now = datetime.now(pytz.timezone('Asia/Jerusalem'))
        seconds = (remind_time - now).total_seconds()
        if seconds > 0:
            threading.Timer(seconds, lambda: bot.send_message(user_id, f"תזכורת: {text}")).start()
    reminder_job()

### 3. זיהוי שמות ואנשי קשר ###
def extract_contact_name(text):
    # Simple heuristic for demo – real-world use NLP/LLM for better extraction
    import re
    match = re.search(r'עם ([^ ]+)', text)
    if match:
        name = match.group(1)
        return name
    return None

def add_contact(user_id, name, info=None):
    user_contacts = contacts.setdefault(str(user_id), {})
    user_contacts[name] = info or {}
    save_data()

### 4. תמיכה בשפה נוספת ###
def detect_language(text):
    try:
        return detect(text)
    except Exception:
        return "he"

def translate_text(text, dest_language):
    try:
        return translator.translate(text, dest=dest_language).text
    except Exception:
        return text

### 5. ניהול משימות מורכבות ###
def get_tasks_for_user(user_id):
    return tasks.get(str(user_id), [])

def add_task(user_id, task, time=None, contact=None, status="pending"):
    user_tasks = tasks.setdefault(str(user_id), [])
    user_tasks.append({"task": task, "time": time, "contact": contact, "status": status})
    save_data()

def update_task_status(user_id, task_index, status):
    user_tasks = tasks.get(str(user_id), [])
    if 0 <= task_index < len(user_tasks):
        user_tasks[task_index]['status'] = status
        save_data()

### 6. שליחת הודעות למשתמשים אחרים (בתוך בוט טלגרם) ###
def send_message_to_user(user_id, text):
    try:
        bot.send_message(user_id, text)
        return True
    except Exception as e:
        print("Send message error:", e)
        return False

### עיבוד פקודות ###
def parse_datetime_from_text(text):
    # Very basic parser: looks for HH:MM and "מחר"
    import re
    now = datetime.now(pytz.timezone("Asia/Jerusalem"))
    hourmin = re.search(r'(\d{1,2}):(\d{2})', text)
    dt = now
    if hourmin:
        dt = dt.replace(hour=int(hourmin.group(1)), minute=int(hourmin.group(2)), second=0, microsecond=0)
    if "מחר" in text:
        dt += timedelta(days=1)
    return dt

def parse_task_command(text):
    # Example: "מאיה, תזכירי לי לדבר עם יוסי מחר ב-10:00"
    import re
    match = re.search(r"תזכירי לי (.+?)(?: ב-(\d{1,2}:\d{2}))?(?: מחר)?", text)
    if match:
        task = match.group(1)
        time = parse_datetime_from_text(text)
        contact = extract_contact_name(text)
        return task, time, contact
    return None, None, None

### LLM Integration ###
def ask_gemini(prompt, user_id=None, lang="he"):
    # Build context
    context = ""
    if user_id:
        profile = user_data.get(str(user_id), {})
        context += f"המשתמש: {profile}\n"
        user_tasks = get_tasks_for_user(user_id)
        if user_tasks:
            context += "משימות קיימות:\n"
            for t in user_tasks:
                context += f"- {t['task']}, ל-{t.get('time', 'לא צויין')}, סטטוס: {t.get('status', 'לא צויין')}\n"
        user_contacts = contacts.get(str(user_id), {})
        if user_contacts:
            context += "אנשי קשר:\n" + ", ".join(user_contacts.keys()) + "\n"
    context += f"משתמש: {prompt}\nמזכירה חכמה, עני בצורה שירותית, קצרה ויעילה. אם מדובר במשימה, תעדכני ביומן המשימות ותציעי תזכורת."
    try:
        response = model.generate_content(context)
        answer = response.text if hasattr(response, 'text') else str(response)
        # Translate if needed
        if lang != "he":
            answer = translate_text(answer, lang)
        # Save chat history
        if user_id:
            user_data.setdefault(str(user_id), {}).setdefault("history", []).append({"user": prompt, "bot": answer})
            save_data()
        return answer
    except Exception as e:
        print("Gemini error:", e)
        return "מצטערת, הייתה בעיה בעיבוד הבקשה. נסה שוב."

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    lang = detect_language(message.text)
    # פקודת תזכורת/משימה חדשה
    task, time, contact = parse_task_command(message.text)
    if task:
        add_task(message.from_user.id, task, str(time), contact)
        # Google Calendar integration
        calendar_resp = add_event_to_calendar(task, time)
        # תזכורת אוטומטית (אם הזמן > עכשיו)
        if time and time > datetime.now(pytz.timezone('Asia/Jerusalem')):
            schedule_reminder(message.chat.id, task, time)
        # הוספת איש קשר במידת הצורך
        if contact:
            add_contact(message.from_user.id, contact)
        answer = f"נוספה משימה: \"{task}\" ל-{time.strftime('%d/%m/%Y %H:%M') if time else 'לא צויין'}\n{calendar_resp}"
        if lang != "he":
            answer = translate_text(answer, lang)
        bot.reply_to(message, answer)
        return

    # פקודת שליחת הודעה למשתמש אחר (דוגמה: "שלחי הודעה ליוסי: ...")
    if "שלחי הודעה ל" in message.text:
        contact = extract_contact_name(message.text)
        msg = message.text.split(":")[-1].strip() if ":" in message.text else "שלום!"
        if contact:
            # נדרש לשייך איש קשר ל-telegram_id (פה רק דמו)
            contact_id = contacts.get(str(message.from_user.id), {}).get(contact, {}).get("telegram_id")
            if contact_id:
                send_message_to_user(contact_id, msg)
                bot.reply_to(message, f"הודעה נשלחה ל-{contact}")
            else:
                bot.reply_to(message, f"לא נמצא מזהה טלגרם לאיש הקשר {contact}.")
            return

    # תשובה חכמה כללית
    bot.send_chat_action(message.chat.id, 'typing')
    answer = ask_gemini(message.text, user_id=message.from_user.id, lang=lang)
    bot.reply_to(message, answer)

class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args): 
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthServer).serve_forever()

def main():
    load_data()
    threading.Thread(target=run_server, daemon=True).start()
    bot.polling()

if __name__ == "__main__":
    main()
