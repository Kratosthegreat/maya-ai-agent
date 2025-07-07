import os
import re
import logging
from datetime import datetime
import requests
import pytz
from flask import Flask, request, jsonify

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY")

# Constants
GOOGLE_AI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaBot:
    def __init__(self):
        self.user_names = {}
        self.conversation_history = {}
        self.rate_limits = {}

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

    def _check_rate_limit(self, user_id):
        now = datetime.now().timestamp()
        self.rate_limits.setdefault(user_id, [])
        self.rate_limits[user_id] = [t for t in self.rate_limits[user_id] if now - t < 60]
        if len(self.rate_limits[user_id]) >= 10:
            return False
        self.rate_limits[user_id].append(now)
        return True

    def process_message(self, user_id, message):
        if not self._check_rate_limit(user_id):
            return "אני צריכה לנוח רגע, נדבר עוד דקה? 😴"

        text_lower = message.lower().strip()

        # Name introduction
        name_patterns = [
            r'(?:שמי|קוראים לי|השם שלי) (?:הוא )?([א-ת\s]{2,15})(?:\s|$|\.)',
            r'אני ([א-ת\s]{2,15})(?:\s|$|\.)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                if name and name not in ["הוא", "היא", "אתה", "את"]:
                    self.user_names[user_id] = name
                    return f"נעים מאוד להכיר אותך, {name}! 😊 אני מאיה."

        # Time queries
        time_phrases = ['מה השעה', 'איזה יום', 'מה התאריך', 'תאריך היום', 
                        'איזה תאריך', 'כמה השעה', 'מה הזמן', 'זמן עכשיו']
        if any(p in text_lower for p in time_phrases):
            time_info = self.get_israel_time()
            return f"🕐 {time_info['full']}"

        # Google AI call
        headers = {
            "Content-Type": "application/json"
        }

        user_name = self.user_names.get(user_id, "")
        name_suffix = f" {user_name}" if user_name else ""

        prompt = f"""את מאיה, המזכירה האישית של{name_suffix}. 
את חכמה, רגישה, ומדברת בעברית בלבד.
את מגיבה כמו אדם חם ונעים.
תעני בקצרה, 1-10 מילים.
תסיימי באימוג'י אחד.
אסור לך להשתמש בביטויים כמו "אני מצטערת", "אני חושבת", "ייתכן ש".

הודעת המשתמש: {message}

תשובתך:"""

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 50,
                "topK": 40,
                "topP": 0.95
            }
        }

        try:
            url = f"{GOOGLE_AI_URL}?key={GOOGLE_API_KEY}"
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            
            if response.status_code != 200:
                logger.error(f"Google AI error: {response.status_code} - {response.text}")
                if response.status_code == 401:
                    return "יש בעיה עם המפתח שלי 🔑"
                elif response.status_code == 429:
                    return "יותר מדי בקשות, נסה בעוד דקה ⏳"
                return "משהו השתבש, בוא ננסה שוב! ✨"

            data = response.json()
            
            if "candidates" in data and data["candidates"]:
                reply = data["candidates"][0]["content"]["parts"][0]["text"]
                return self._clean_response(reply)
            else:
                return "לא הצלחתי להבין, תנסה שוב? 🤔"

        except requests.exceptions.Timeout:
            return "לוקח לי זמן לחשוב... נסה שוב ⏳"
        except Exception as e:
            logger.error(f"Exception: {e}")
            return "משהו השתבש, אבל אני איתך 🛠️"

    def _clean_response(self, text):
        # Remove forbidden phrases
        forbidden = [r'אני מצטערת', r'אני חושבת', r'ייתכן ש', r'אני לא בטוחה']
        for f in forbidden:
            text = re.sub(f, '', text, flags=re.IGNORECASE)

        text = " ".join(text.split())
        text = re.sub(r'^[.,;!?-]+', '', text).strip()
        text = re.sub(r'[.,;!?-]+$', '', text).strip()

        words = text.split()
        if not words or len(text) < 3:
            return "היי! איך אני יכולה לעזור? 😊"
        if len(words) > 10:
            text = " ".join(words[:10])

        # Add emoji if missing
        if not any(char in text for char in "😊😴⏳✨🔑🤔🛠️💪🫂👍🕐"):
            text += " 😊"

        return text.strip()

maya = MayaBot()

def send_message(chat_id, text):
    try:
        response = requests.post(
            TELEGRAM_API_URL,
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

@app.route("/")
def home():
    time_info = maya.get_israel_time()
    return jsonify({
        "status": "🤖 Maya Bot - Google AI",
        "time": time_info["full"],
        "users": len(maya.conversation_history),
        "api": "Google AI Studio",
        "version": "4.0"
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    if WEBHOOK_SECRET_TOKEN:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not token or token != WEBHOOK_SECRET_TOKEN:
            return "Unauthorized", 403

    try:
        update = request.get_json()
        if not update or "message" not in update:
            return "OK"

        message = update["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")
        
        if chat_id and text and user_id:
            reply = maya.process_message(user_id, text)
            send_message(chat_id, reply)
        
        return "OK"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "OK"

@app.route("/test")
def test():
    return jsonify({
        "status": "Google AI Test",
        "greeting": maya.process_message(999, "שלום מאיה!"),
        "time": maya.process_message(999, "מה השעה?")
    })

if __name__ == "__main__":
    logger.info("🚀 Maya Bot with Google AI Studio")
    app.run(host="0.0.0.0", port=PORT, debug=False)
