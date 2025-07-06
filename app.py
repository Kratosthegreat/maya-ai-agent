import os
import re
import logging
from datetime import datetime
import requests
import pytz
from flask import Flask, request, jsonify

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.getenv("PORT", 10000))

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaBot:
    def __init__(self):
        self.user_names = {}

    def get_israel_time(self):
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        hebrew_days = {
            'Monday': 'שני', 'Tuesday': 'שלישי', 'Wednesday': 'רביעי',
            'Thursday': 'חמישי', 'Friday': 'שישי', 'Saturday': 'שבת', 'Sunday': 'ראשון'
        }
        day_name = hebrew_days.get(now.strftime('%A'), now.strftime('%A'))
        return {
            'time': now.strftime('%H:%M'),
            'date': now.strftime('%d/%m/%Y'),
            'day': day_name,
            'full': f"יום {day_name}, {now.strftime('%d/%m/%Y')} בשעה {now.strftime('%H:%M')}"
        }

    def process_message(self, user_id, message):
        # Detect and save name
        name_patterns = [
            r'שמי (?:הוא )?(.{1,15})(?:\s|$|\.)',
            r'קוראים לי (.{1,15})(?:\s|$|\.)',
            r'השם שלי (?:הוא )?(.{1,15})(?:\s|$|\.)',
            r'אני (.{1,15})(?:\s|$|\.)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                if name and len(name) < 15:
                    self.user_names[user_id] = name
                    return f"נעים מאוד להכיר אותך, {name}! 😊 אני מאיה, העוזרת הדיגיטלית שלך."

        user_name = self.user_names.get(user_id, "")
        name_suffix = f" {user_name}" if user_name else ""

        system_prompt = f"""
        את מאיה, המזכירה האישית של דוד. את חכמה, רגישה, מבינה רמזים רגשיים, מדברת בעברית בלבד.
        את לא רובוט – את מגיבה כמו אדם חם, נעים, מצחיק לפעמים, או מרגיעה כשצריך.
        את זוכרת שהשם של המשתמש הוא{name_suffix}.
        אם הוא שואל שאלה פשוטה – תעני ישר ולעניין.
        אם הוא מרגיש תקוע, עייף או מתוסכל – תגיבי בהתאם ברגישות.
        """

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://maya-bot.onrender.com"
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        }

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            return reply.strip()
        except Exception as e:
            logger.error(f"OpenRouter GPT error: {e}")
            return "מצטערת, משהו לא עבד כרגע. תוכל לנסח שוב?"

maya = MayaBot()

def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False

@app.route("/")
def home():
    time_info = maya.get_israel_time()
    return jsonify({
        "status": "🤖 Maya Bot - GPT via OpenRouter",
        "current_time": time_info['full'],
        "users_with_names": len(maya.user_names),
        "features": [
            "✅ GPT (3.5-turbo) עם עברית טבעית",
            "✅ הבנה רגשית והקשרית",
            "✅ שמירת שמות משתמשים",
            "✅ בוט רגיש וחם, לא רובוטי"
        ]
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        if not update or "message" not in update:
            return "OK"
        message = update["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")
        if chat_id and text and user_id:
            logger.info(f"User {user_id}: {text[:40]}...")
            response = maya.process_message(user_id, text)
            logger.info(f"Response: {response[:40]}...")
            send_message(chat_id, response)
        return "OK"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ERROR"

@app.route("/test")
def test():
    return jsonify({
        "message": maya.process_message(123, "אני מרגיש תקוע היום"),
    })

if __name__ == "__main__":
    logger.info("🚀 Maya Bot is running with GPT via OpenRouter (gpt-3.5-turbo)")
    app.run(host="0.0.0.0", port=PORT, debug=False)
