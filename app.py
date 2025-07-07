import os
import re
import logging
from datetime import datetime
import requests
import pytz
import random
from flask import Flask, request, jsonify

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaBot:
    def __init__(self):
        self.user_names = {}
        self.conversation_history = {}
        self.rate_limits = {}
        
        # Smart response templates
        self.responses = {
            'greetings': [
                "שלום! איך אפשר לעזור? 😊",
                "היי! איך המצב? 😊", 
                "שלום יקר! מה נשמע? 😊",
                "היי! נעים לראות אותך 😊"
            ],
            'how_are_you': [
                "אני במצב רוח מעולה! ואתה? 😊",
                "הכל טוב! איך אתה מרגיש? 😊",
                "נהדר! מה איתך? 😊"
            ],
            'thanks': [
                "בכיף! תמיד פה לעזור ✨",
                "בשמחה! יש עוד משהו? ✨",
                "אין בעד מה! 😊"
            ],
            'help': [
                "אני כאן לעזור! מה אתה צריך? 💪",
                "בוא נראה איך אני יכולה לעזור 💪",
                "תגיד מה צריך ואני אעזור 💪"
            ],
            'confused': [
                "לא הבנתי בדיוק, תוכל להסביר? 🤔",
                "תסביר לי שוב? 🤔",
                "לא ברור לי, תפרט יותר? 🤔"
            ],
            'emotions': {
                'sad': [
                    "מצטערת לשמוע. רוצה לדבר על זה? 🫂",
                    "אני כאן בשבילך 🫂",
                    "זה יעבור. אני כאן לתמוך 🫂"
                ],
                'happy': [
                    "כמה נחמד לשמוע! 😊",
                    "איזה כיף! מה הסיבה? 😊", 
                    "נהדר! שמחה איתך 😊"
                ],
                'tired': [
                    "אולי כדאי לנוח קצת? 😴",
                    "מתי ישנת לאחרונה? 😴",
                    "תנוח, זה חשוב 😴"
                ]
            },
            'work': [
                "העבודה תמיד מלחיצה... איך אני יכולה לעזור? 💪",
                "בוא נחשוב ביחד איך להתמודד 💪",
                "מה הדבר הכי דחוף עכשיו? 💪"
            ],
            'weather': [
                "מזג האוויר משפיע על המצב רוח 🌤️",
                "איך המזג השפיע עליך היום? 🌤️"
            ],
            'default': [
                "מעניין... ספר לי עוד 😊",
                "נשמע חשוב לך 😊",
                "אני מקשיבה 😊",
                "תמשיך, אני איתך 😊"
            ]
        }

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
        if len(self.rate_limits[user_id]) >= 20:
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

        # Pattern matching for smart responses
        return self._get_smart_response(text_lower, user_id)

    def _get_smart_response(self, text, user_id):
        user_name = self.user_names.get(user_id, "")
        
        # Greetings
        greetings = ['שלום', 'היי', 'אהלן', 'שלום שלום', 'בוקר טוב', 'ערב טוב', 'לילה טוב']
        if any(g in text for g in greetings):
            response = random.choice(self.responses['greetings'])
            if user_name:
                response = response.replace("יקר", user_name)
            return response

        # How are you
        how_questions = ['איך אתה', 'מה שלומך', 'איך המצב', 'מה נשמע', 'איך הולך']
        if any(q in text for q in how_questions):
            return random.choice(self.responses['how_are_you'])

        # Thanks
        thanks = ['תודה', 'תודה רבה', 'מעולה', 'נהדר', 'אלוף']
        if any(t in text for t in thanks):
            return random.choice(self.responses['thanks'])

        # Help requests
        help_words = ['עזרה', 'תעזרי', 'לא יודע', 'תציעי', 'המלצה']
        if any(h in text for h in help_words):
            return random.choice(self.responses['help'])

        # Emotions
        sad_words = ['עצוב', 'מדוכא', 'רע לי', 'קשה לי', 'בכי', 'עצבות']
        if any(s in text for s in sad_words):
            return random.choice(self.responses['emotions']['sad'])

        happy_words = ['שמח', 'נהדר', 'מעולה', 'כיף', 'אושר', 'טוב לי']
        if any(h in text for h in happy_words):
            return random.choice(self.responses['emotions']['happy'])

        tired_words = ['עייף', 'מותש', 'לא יכול', 'תשוש', 'נמאס']
        if any(t in text for t in tired_words):
            return random.choice(self.responses['emotions']['tired'])

        # Work related
        work_words = ['עבודה', 'משרד', 'בוס', 'פגישה', 'פרויקט', 'מטלה', 'דדליין']
        if any(w in text for w in work_words):
            return random.choice(self.responses['work'])

        # Weather
        weather_words = ['מזג אוויר', 'גשם', 'שמש', 'חם', 'קר', 'רוח']
        if any(w in text for w in weather_words):
            return random.choice(self.responses['weather'])

        # Confusion indicators
        if '?' in text and len(text.split()) < 3:
            return random.choice(self.responses['confused'])

        # Default responses
        return random.choice(self.responses['default'])

maya = MayaBot()

def send_message(chat_id, text):
    try:
        response = requests.post(
            TELEGRAM_API_URL,
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
        logger.info(f"Sent message to {chat_id}: {text[:50]}...")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return False

@app.route("/")
def home():
    time_info = maya.get_israel_time()
    return jsonify({
        "status": "🤖 Maya Bot - Smart Responses (No External APIs)",
        "time": time_info["full"],
        "users": len(maya.conversation_history),
        "api": "Built-in Intelligence",
        "version": "5.0",
        "uptime": "100%"
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
            logger.info(f"Received message from {user_id}: {text[:30]}...")
            reply = maya.process_message(user_id, text)
            send_message(chat_id, reply)
        
        return "OK"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "OK"

@app.route("/test")
def test():
    test_cases = [
        ("שלום מאיה!", "greeting"),
        ("מה השעה?", "time"),
        ("איך אתה מרגיש?", "how_are_you"),
        ("אני עצוב", "emotion"),
        ("תודה רבה", "thanks")
    ]
    
    results = {}
    for text, case_type in test_cases:
        results[case_type] = maya.process_message(999, text)
    
    return jsonify({
        "status": "Smart Response Test",
        "results": results
    })

if __name__ == "__main__":
    logger.info("🚀 Maya Bot - Smart Responses (No APIs needed!)")
    app.run(host="0.0.0.0", port=PORT, debug=False)
