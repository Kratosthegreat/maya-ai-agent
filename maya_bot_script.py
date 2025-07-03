import os
import json
from datetime import datetime
import pytz
from flask import Flask, request
import telebot
import google.generativeai as genai

# =========================
# Environment Variables
# =========================
def get_env_var(name, required=True, default=None):
    value = os.environ.get(name, default)
    if required and value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

TELEGRAM_TOKEN = get_env_var("TELEGRAM_TOKEN")
WEBHOOK_URL = get_env_var("WEBHOOK_URL")
GEMINI_API_KEY = get_env_var("GEMINI_API_KEY")

# =========================
# Setup
# =========================
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

user_data = {}
chat_sessions = {}

# =========================
# Data Storage
# =========================
def load_data():
    global user_data, chat_sessions
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            user_data = data.get("user_data", {})
        print(f"Loaded data for {len(user_data)} users")
    except Exception:
        user_data = {}
        print("Created new data storage")

def save_data():
    try:
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump({
                "user_data": user_data
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving data:", e)

# =========================
# Utility Functions
# =========================
def get_time_israel():
    tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(tz)
    return now.strftime("%H:%M"), now.strftime("%A %d/%m/%Y")

def extract_user_info(user_id, text):
    user_id = str(user_id)
    if user_id not in user_data:
        user_data[user_id] = {}

    if "קוראים לי" in text:
        try:
            parts = text.split("קוראים לי")
            if len(parts) > 1:
                name = parts[1].strip().split()[0]
                user_data[user_id]["שם"] = name.replace(",", "").replace(".", "")
                save_data()
                print(f"Saved name: {user_data[user_id]['שם']}")
                return True
        except:
            pass

    if any(word in text for word in ["עובד ב", "עובדת ב", "עבודה ב"]):
        user_data[user_id]["עבודה"] = text[:100]
        save_data()
        return True

    return False

def quick_answers(text):
    text_lower = text.lower()
    if any(phrase in text_lower for phrase in ["מה השעה", "איזה שעה", "כמה השעה"]):
        time_now, _ = get_time_israel()
        return f"🕐 השעה עכשיו בישראל: {time_now}"
    if any(phrase in text_lower for phrase in ["מה התאריך", "איזה תאריך", "מה היום"]):
        _, date_now = get_time_israel()
        return f"📅 התאריך היום: {date_now}"
    if "מזג אוויר" in text_lower:
        if "ניו יורק" in text_lower:
            return "🌤️ בניו יורק בחורף קר (בערך 5°C) ובקיץ חם (בערך 25°C)"
        elif "תל אביב" in text_lower:
            return "☀️ בתל אביב בדרך כלל חם ושמש, בחורף 18°C ובקיץ 30°C"
        else:
            return "🌍 איזו עיר אתה רוצה לדעת?"
    return None

def create_smart_prompt(user_id):
    time_now, date_now = get_time_israel()
    user_info = user_data.get(str(user_id), {})
    user_name = user_info.get("שם", "חבר")

    prompt = f"""את מאיה - עוזרת אישית חכמה וחמודה! 🌟

זמן עכשיו: {time_now}
תאריך היום: {date_now}
מיקום: ישראל

המשתמש: {user_name}
מידע שיש לי עליו: {json.dumps(user_info, ensure_ascii=False)}

התפקיד שלך:
1. תני תשובות קצרות וחכמות (1-2 שורות בלבד!)
2. השתמשי בשם {user_name} כשמתאים
3. תהיי חמודה אבל לא מוגזמת
4. תני עצות מעשיות וחכמות
5. זכרי מידע חשוב שהמשתמש אומר

תגיבי בצורה אישית, חכמה וחמה!"""
    return prompt

def get_gemini_response(user_id, message_text):
    try:
        # Start new chat session if not exists
        if user_id not in chat_sessions:
            chat_sessions[user_id] = model.start_chat(history=[])
            chat_sessions[user_id].send_message(create_smart_prompt(user_id))
        response = chat_sessions[user_id].send_message(message_text)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        chat_sessions[user_id] = model.start_chat(history=[])
        return "😅 סליחה, קרתה לי שגיאה קטנה. אפשר לנסות שוב?"

# =========================
# Bot Handlers
# =========================

@bot.message_handler(commands=["start"])
def start_command(message):
    bot.reply_to(message, """🌟 היי! אני מאיה - העוזרת החכמה שלך!

אני יכולה:
🕐 לענות על "מה השעה?"
📅 לזכור את השם שלך
🧠 לנהל שיחה חכמה
⚡ לעזור בכל שאלה

פשוט כתוב לי משהו ונתחיל!""")

@bot.message_handler(commands=["memory"])
def memory_command(message):
    user_id = str(message.from_user.id)
    info = user_data.get(user_id, {})
    if info:
        text = "🧠 מה שאני זוכרת עליך:\n"
        for key, value in info.items():
            text += f"• {key}: {value}\n"
        bot.reply_to(message, text)
    else:
        bot.reply_to(message, "🤔 עדיין לא זכרתי עליך הרבה. ספר לי על עצמך!")

@bot.message_handler(commands=["forget"])
def forget_command(message):
    user_id = str(message.from_user.id)
    if user_id in user_data:
        del user_data[user_id]
        save_data()
    if user_id in chat_sessions:
        del chat_sessions[user_id]
    bot.reply_to(message, "🧹 שכחתי הכל עליך! בואו נכיר מחדש!")

@bot.message_handler(commands=["refresh"])
def refresh_command(message):
    user_id = str(message.from_user.id)
    if user_id in chat_sessions:
        del chat_sessions[user_id]
    bot.reply_to(message, "🔄 רעננתי את הזיכרון! עכשיו אני זוכרת הכל טוב יותר!")

@bot.message_handler(commands=["time"])
def time_command(message):
    time_now, date_now = get_time_israel()
    bot.reply_to(message, f"🕐 {time_now}\n📅 {date_now}")

# ** סינון בוטים! ** (כולל הבוט עצמו)
@bot.message_handler(func=lambda m: not getattr(m.from_user, "is_bot", False))
def handle_message(message):
    try:
        user_id = str(message.from_user.id)
        text = message.text
        print(f"Message from {user_id}: {text}")

        quick_answer = quick_answers(text)
        if quick_answer:
            bot.reply_to(message, quick_answer)
            print("Quick answer sent")
            return

        info_saved = extract_user_info(user_id, text)
        if info_saved and user_id in chat_sessions:
            del chat_sessions[user_id]

        bot.send_chat_action(message.chat.id, "typing")
        response_text = get_gemini_response(user_id, text)
        bot.reply_to(message, response_text)
        print("Gemini response sent")

    except Exception as e:
        print(f"Error in handle_message: {e}")
        bot.reply_to(message, "😅 אופס! משהו לא עבד. בואו ננסה שוב?")

# =========================
# Webhook & Health
# =========================

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
        print("Old webhook removed")
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"Webhook set to: {WEBHOOK_URL}")
    except Exception as e:
        print(f"Webhook setup error: {e}")
    print("Maya ready! 🌟")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()
