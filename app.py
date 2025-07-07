import os
import re
import logging
from datetime import datetime
import requests
import pytz
import threading
from flask import Flask, request, jsonify

# Config - Load from environment with validation
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN in environment variables")

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
if not HUGGINGFACE_API_KEY:
    raise ValueError("Missing HUGGINGFACE_API_KEY in environment variables")

PORT = int(os.getenv("PORT", 10000))
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")
if not WEBHOOK_SECRET_TOKEN:
    logging.warning("Running without WEBHOOK_SECRET_TOKEN - not recommended for production")

HF_API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
MAX_HISTORY_LENGTH = 10
REQUEST_TIMEOUT = 30

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
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return "אני צריכה לנוח רגע, נדבר עוד דקה? 😴"

        text_lower = message.lower().strip()

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
                    self._add_to_history(user_id, "user", message)
                    response = f"נעים מאוד להכיר אותך, {name}! 😊 אני מאיה, העוזרת הדיגיטלית שלך."
                    self._add_to_history(user_id, "assistant", response)
                    return response

        time_phrases = ['מה השעה', 'איזה יום', 'מה התאריך', 'תאריך היום', 
                        'איזה תאריך', 'כמה השעה', 'מה הזמן', 'זמן עכשיו']
        if any(p in text_lower for p in time_phrases):
            time_info = self.get_israel_time()
            self._add_to_history(user_id, "user", message)
            response = f"🕐 {time_info['full']}"
            self._add_to_history(user_id, "assistant", response)
            return response

        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        payload = {
            "inputs": f"משתמש: {message}\nמאיה:",
            "parameters": {
                "max_new_tokens": 50,
                "temperature": 0.7,
                "do_sample": True
            }
        }

        try:
            res = requests.post(HF_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
            if res.status_code != 200:
                logger.error(f"HuggingFace error {res.status_code}: {res.text}")
                if res.status_code == 401:
                    return "יש בעיה עם המפתח שלי 🔑"
                elif res.status_code == 429:
                    return "יותר מדי בקשות, נסה בעוד דקה ⏳"
                elif res.status_code == 503:
                    return "השירות עמוס, נסה בעוד דקה 🔄"
                return "משהו השתבש, ננסה שוב ✨"

            data = res.json()
            reply = data[0].get("generated_text", "") if isinstance(data, list) else str(data)
            if "מאיה:" in reply:
                reply = reply.split("מאיה:")[-1].strip()

            cleaned = self._clean_llm_response(reply)
            self._add_to_history(user_id, "user", message)
            self._add_to_history(user_id, "assistant", cleaned)
            return cleaned

        except requests.exceptions.Timeout:
            return "לוקח לי זמן לחשוב... נסה שוב ⏳"
        except Exception as e:
            logger.error(f"Exception: {e}")
            return "משהו השתבש, אבל אני איתך 🛠️"

    def _add_to_history(self, user_id, role, content):
        self.conversation_history.setdefault(user_id, []).append({"role": role, "content": content})
        self.conversation_history[user_id] = self.conversation_history[user_id][-MAX_HISTORY_LENGTH:]

    def _clean_llm_response(self, text):
        forbidden = [r'אני מצטערת', r'אני חושבת', r'ייתכן ש', r'אני לא בטוחה', r'כמודל שפה']
        for f in forbidden:
            text = re.sub(f, '', text, flags=re.IGNORECASE)

        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'[*_`]', '', text)
        text = " ".join(text.split())
        text = re.sub(r'^[.,;!?-]+', '', text).strip()
        text = re.sub(r'[.,;!?-]+$', '', text).strip()

        words = text.split()
        if not words or len(text) < 3:
            return "היי! איך אני יכולה לעזור? 😊"
        if len(words) > 10:
            text = " ".join(words[:10])

        emoji = "👍"
        lower = text.lower()
        if any(w in lower for w in ["נעים", "כיף", "טוב", "שמחה"]):
            emoji = "😊"
        elif any(w in lower for w in ["תודה", "בכיף"]):
            emoji = "✨"
        elif any(w in lower for w in ["שעה", "תאריך"]):
            emoji = "🕐"
        elif any(w in lower for w in ["עזרה", "לעזור"]):
            emoji = "💪"
        elif any(w in lower for w in ["לא מבין", "???", "!!!"]):
            emoji = "🤔"
        elif any(w in lower for w in ["תקוע", "עייף", "מתוסכל"]):
            emoji = "🫂"
        return f"{text} {emoji}".strip()

maya = MayaBot()

def send_message(chat_id, text):
    try:
        res = requests.post(
            TELEGRAM_API_URL,
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
        if res.status_code != 200:
            logger.error(f"Telegram error: {res.status_code} - {res.text}")
            return False
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False

@app.route("/")
def home():
    time_info = maya.get_israel_time()
    return jsonify({
        "status": "🤗 Maya Bot - HuggingFace",
        "time": time_info["full"],
        "users": len(maya.conversation_history),
        "model": "DialoGPT-medium",
        "version": "3.0"
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    if WEBHOOK_SECRET_TOKEN:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not token or token != WEBHOOK_SECRET_TOKEN:
            return "Unauthorized", 403

    update = request.get_json()
    if not update or "message" not in update:
        return "OK"

    # Reply to Telegram immediately
    def async_handler():
        try:
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            user_id = message.get("from", {}).get("id")
            if chat_id and text and user_id:
                reply = maya.process_message(user_id, text)
                send_message(chat_id, reply)
        except Exception as e:
            logger.error(f"Async handler error: {e}")

    threading.Thread(target=async_handler).start()
    return jsonify({"status": "accepted"})

if __name__ == "__main__":
    logger.info("🚀 Maya Bot running on HuggingFace")
    app.run(host="0.0.0.0", port=PORT, debug=False)
