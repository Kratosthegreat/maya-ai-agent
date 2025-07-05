# === מאיה 3.0 - גרסה מתוקנת ===
import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests
import pytz
from typing import Dict, Any, Optional
import time
import re

# Third-party imports
import google.generativeai as genai
from config import config

# === LOGGING ===
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# === DATA STORAGE ===
DATA_FILE = "maya_data.json"
GEMINI_USAGE_FILE = "gemini_usage.json"
user_data = {}
conversations = {}
memories = {}

def load_data():
    global user_data, conversations, memories
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_data = data.get('users', {})
                conversations = data.get('conversations', {})
                memories = data.get('memories', {})
                logger.info(f"Loaded data for {len(user_data)} users")
        else:
            logger.info("No existing data file, starting fresh")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        user_data = {}
        conversations = {}
        memories = {}

def save_data():
    try:
        data = {
            'users': user_data,
            'conversations': conversations,
            'memories': memories,
            'last_updated': datetime.now().isoformat()
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug("Data saved successfully")
    except Exception as e:
        logger.error(f"Error saving data: {e}")

load_data()

# === CLAUDE-LIKE INTELLIGENCE ENGINE ===
class ClaudeIntelligenceEngine:
    """מנוע חכמה שמחקה בדיוק את Claude"""
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        self.built_in_knowledge = {
            "israel_current_war": {
                "name": "מלחמת חרבות ברזל",
                "start": "7 באוקטובר 2023",
                "against": "חמאס",
                "status": "מתמשכת",
                "quick_answer": "המלחמה האחרונה של ישראל היא מלחמת חרבות ברזל שהחלה ב-7 באוקטובר 2023 עם התקפת הטרור של חמאס."
            },
            "world_cup_2026": {
                "year": 2026,
                "hosts": ["ארצות הברית", "מקסיקו", "קנדה"],
                "teams": 48,
                "quick_answer": "המונדיאל הבא יתקיים ב-2026 בארצות הברית, מקסיקו וקנדה עם 48 נבחרות."
            },
            "olympics_2028": {
                "year": 2028,
                "host": "לוס אנג'לס",
                "season": "קיץ",
                "quick_answer": "האולימפיאדה הבאה תהיה ב-2028 בלוס אנג'לס."
            },
            "us_president": {
                "name": "דונלד טראמפ",
                "elected": "נובמבר 2024",
                "inaugurated": "ינואר 2025",
                "quick_answer": "הנשיא הנוכחי של ארצות הברית הוא דונלד טראמפ (נבחר בנובמבר 2024)."
            }
        }

        self.recognition_patterns = {
            "greeting": [
                r"^(היי|שלום|hello|hi)\s*(מאיה)?$",
                r"^(בוקר טוב|ערב טוב|לילה טוב)$"
            ],
            "how_are_you": [
                r"(מה שלומך|איך אתה|איך את|מה נשמע|איך הולך)",
                r"(how are you|how's it going|what's up)"
            ],
            "israel_war": [
                r"(מלחמה|מלחמת).*(אחרון|עכשיו|נוכחי|היום|ישראל)",
                r"המלחמה.*(של ישראל|בישראל|עכשיו)",
                r"(7 באוקטובר|שבעה באוקטובר|חרבות ברזל)",
                r"(חמאס|עזה|דרום).*(מלחמה|קרב)"
            ],
            "world_cup": [
                r"(מונדיאל|world cup).*(הבא|2026|מתי)",
                r"(כדורגל|פוטבול).*(עולם|מונדיאל)"
            ],
            "olympics": [
                r"(אולימפיאדה|olympics).*(הבא|2028|מתי)",
                r"(משחקים אולימפיים)"
            ],
            "us_president": [
                r"(נשיא|president).*(אמריקה|ארצות הברית|אמריקאי)",
                r"(טראמפ|trump)",
                r"מי (נשיא|מנהל|בראש).*(אמריקה|ארצות הברית)"
            ],
            "weather": [
                r"(מזג אוויר|טמפרטורה|חם|קר|מעלות|גשם|שמש)",
                r"מה (הטמפרטורה|המזג|מזג האוויר)",
                r"(טמפרטורה|מזג אוויר).*(ב|של|עכשיו)",
                r"כמה מעלות",
                r"איך (המזג|מזג האוויר|הטמפרטורה)"
            ],
            "time": [
                r"(שעה|זמן|מתי עכשיו)"
            ]
        }

    def analyze_and_respond(self, message: str) -> Dict[str, Any]:
        message_lower = message.lower().strip()
        for topic, patterns in self.recognition_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    logger.info(f"Detected topic: {topic}")
                    return self._get_built_in_response(topic, message)
        return {
            "type": "needs_ai_or_search",
            "confidence": "low",
            "response": None
        }

    def _get_built_in_response(self, topic: str, original_message: str) -> Dict[str, Any]:
        if topic == "greeting":
            response = "היי! 👋"
        elif topic == "how_are_you":
            response = "בסדר גמור! 😊"
        elif topic == "israel_war":
            response = "מלחמת חרבות ברזל - המלחמה שהחלה ב-7 באוקטובר 2023 כשחמאס תקף את ישראל. זו המלחמה הנוכחית של ישראל."
        elif topic == "world_cup":
            response = "המונדיאל הבא ב-2026! 🏆\nארצות הברית, מקסיקו וקנדה יארחו יחד.\n48 נבחרות במקום 32 - המונדיאל הגדול ביותר בהיסטוריה."
        elif topic == "olympics":
            response = "אולימפיאדת הקיץ הבאה ב-2028 בלוס אנג'לס! 🏅\nהשלישית שלהם בעיר הזו."
        elif topic == "us_president":
            response = "דונלד טראמפ הוא הנשיא הנוכחי של ארצות הברית. נבחר בנובמבר 2024 ונכנס לתפקיד בינואר 2025."
        elif topic == "weather":
            return {
                "type": "weather_service",
                "confidence": "high",
                "response": None
            }
        elif topic == "time":
            return {
                "type": "time_service",
                "confidence": "high",
                "response": None
            }
        else:
            response = "אין מידע זמין"
        return {
            "type": "direct_answer",
            "confidence": "high",
            "response": response,
            "source": "built_in_knowledge"
        }

# === GEMINI TRACKER ===
class GeminiTracker:
    def __init__(self):
        self.usage_file = GEMINI_USAGE_FILE
        self.daily_limit = 1500
        self.minute_limit = 15
        self.load_usage_data()

    def load_usage_data(self):
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    self.usage_data = json.load(f)
            except:
                self._init_usage_data()
        else:
            self._init_usage_data()

    def _init_usage_data(self):
        self.usage_data = {
            'daily_requests': 0,
            'last_reset': str(datetime.now().date()),
            'minute_requests': [],
            'total_tokens': 0,
            'total_requests_ever': 0
        }

    def save_usage_data(self):
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage: {e}")

    def can_make_request(self):
        today = str(datetime.now().date())
        if self.usage_data['last_reset'] != today:
            self.usage_data['daily_requests'] = 0
            self.usage_data['last_reset'] = today
            self.usage_data['minute_requests'] = []

        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        self.usage_data['minute_requests'] = [
            req_time for req_time in self.usage_data['minute_requests']
            if datetime.fromisoformat(req_time) > minute_ago
        ]

        if self.usage_data['daily_requests'] >= self.daily_limit:
            return False, f"הגעת למגבלה היומית ({self.daily_limit})"
        if len(self.usage_data['minute_requests']) >= self.minute_limit:
            return False, f"יותר מדי בקשות בדקה ({self.minute_limit})"

        return True, "OK"

    def record_request(self, tokens_used=0):
        now = datetime.now()
        self.usage_data['daily_requests'] += 1
        self.usage_data['total_requests_ever'] += 1
        self.usage_data['minute_requests'].append(now.isoformat())
        self.usage_data['total_tokens'] += tokens_used
        self.save_usage_data()

    def get_usage_stats(self):
        return {
            'daily_requests': self.usage_data['daily_requests'],
            'daily_limit': self.daily_limit,
            'daily_remaining': self.daily_limit - self.usage_data['daily_requests'],
            'total_tokens': self.usage_data['total_tokens'],
            'total_requests_ever': self.usage_data['total_requests_ever'],
            'percentage_used_today': round((self.usage_data['daily_requests'] / self.daily_limit) * 100, 1)
        }

# === CLAUDE-STYLE AI SERVICE ===
class ClaudeStyleAI:
    """שירות AI שמחקה את Claude בדיוק"""
    def __init__(self):
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            self.chat_sessions = {}
            self.intelligence_engine = ClaudeIntelligenceEngine()
            self.tracker = GeminiTracker()
            self.system_prompt = """את מאיה - עוזרת AI פשוטה וישירה.

חוקים קריטיים:
1. אל תברכי אוטומטית! אל תגידי "שלום" או "היי" אלא אם המשתמש בירך קודם
2. תשובות קצרות - משפט אחד או שניים לכל היותר
3. אל תשאלי שאלות מיותרות כמו "מה שלומך?" או "איך אני יכולה לעזור?"
4. תני תשובות ישירות ולעניין
5. אל תכפילי הודעות

דוגמאות:
שאלה: "מה שלומך?"
תשובה: "בסדר גמור! 😊"

שאלה: "היי מאיה"  
תשובה: "היי! 👋"

שאלה: "מתי המונדיאל הבא?"
תשובה: "ב-2026 בארצות הברית, מקסיקו וקנדה 🏆"

תגיבי רק למה שנשאל ותהיי קצרה ומדויקת."""
            logger.info("Claude-style AI Service initialized")
        except Exception as e:
            logger.error(f"AI Service initialization failed: {e}")
            raise

    def generate_response(self, user_id: str, message: str, context: str = "") -> str:
        try:
            can_request, status_message = self.tracker.can_make_request()
            if not can_request:
                return f"יותר מדי בקשות היום. נסה מאוחר יותר! 😊"

            intelligence_result = self.intelligence_engine.analyze_and_respond(message)
            if intelligence_result["type"] == "direct_answer":
                self.tracker.record_request(0)
                return intelligence_result["response"]

            elif intelligence_result["type"] == "weather_service":
                location = self._extract_location(message)
                return weather_service.get_weather_anywhere(location)

            elif intelligence_result["type"] == "time_service":
                return self._get_current_time()

            else:
                return self._generate_ai_response(message, context, user_id)
        except Exception as e:
            logger.error(f"Generate response error: {e}")
            return "משהו השתבש. בוא ננסה שוב? 🤔"

    def _extract_location(self, message: str) -> str:
        clean_text = message.replace("מזג אוויר", "").replace("טמפרטורה", "")
        clean_text = clean_text.replace("מה ה", "").replace("מה ", "")
        clean_text = clean_text.replace("ב", "").replace("של", "").replace("את", "")
        clean_text = clean_text.replace("עכשיו", "").replace("היום", "")
        clean_text = clean_text.strip()

        israeli_cities = ["חיפה", "תל אביב", "ירושלים", "באר שבע", "אילת", "נצרת", "טבריה", "צפת", "אשדוד", "אשקלון", "רמת גן", "פתח תקווה", "נתניה", "הרצליה", "רעננה", "כפר סבא", "רמלה", "לוד"]
        for city in israeli_cities:
            if city in message:
                return city

        if not clean_text or len(clean_text) < 2:
            return "תל אביב"
        return clean_text

    def _get_current_time(self) -> str:
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        return f"🕐 {now.strftime('%H:%M')}"

    def _generate_ai_response(self, message: str, context: str, user_id: str) -> str:
        enhanced_message = f"""
        {self.system_prompt}
        הקשר משתמש: {context}
        הודעת המשתמש: {message}
        תני תשובה קצרה וטבעית כמו Claude.
        """
        try:
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
            chat = self.chat_sessions[user_id]
            response = chat.send_message(enhanced_message)
            self.tracker.record_request(len(response.text))
            cleaned_response = self._clean_ai_response(response.text)
            return cleaned_response
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return "לא הצלחתי לעבד את זה. נסה שאלה אחרת 🤔"

    def _clean_ai_response(self, response: str) -> str:
        unwanted_starts = ["שלום דוד", "שלום!", "היי!", "הי דוד", "היי דוד", "שמחה לעזור", "אני כאן בשבילך", "🤖 היי David! אני מאיה", "היי David!", "אני מאיה"]
        for unwanted in unwanted_starts:
            if response.strip().startswith(unwanted):
                response = response.replace(unwanted, "").strip()
                if response.startswith(","):
                    response = response[1:].strip()
                if response.startswith("!"):
                    response = response[1:].strip()
        unwanted_endings = ["מה שלומך?", "איך אני יכולה לעזור?", "איך אוכל לעזור?", "מה אתה צריך?", "במה אוכל לסייע?"]
        for unwanted in unwanted_endings:
            if response.strip().endswith(unwanted):
                response = response.replace(unwanted, "").strip()
        sentences = response.split('.')
        if len(sentences) > 2:
            response = '. '.join(sentences[:2]) + '.'
        response = ' '.join(response.split())
        if not response.strip():
            response = "אוקיי 👍"
        return response.strip()

    def get_usage_stats(self):
        return self.tracker.get_usage_stats()

# === WEATHER SERVICE ===
class GlobalWeatherService:
    def extract_location(self, text: str) -> str:
        text = text.replace("מזג אוויר", "").replace("טמפרטורה", "")
        text = text.replace("ב", "").replace("של", "").replace("את", "")
        text = text.strip()
        if not text or len(text) < 2:
            return "תל אביב"
        return text

    def get_weather_anywhere(self, location: str) -> str:
        try:
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=he&format=json"
            geo_response = requests.get(geocoding_url, timeout=5)
            geo_data = geo_response.json()

            if not geo_data.get('results'):
                return f"לא מצאתי את '{location}'. נסה שם אחר 🌍"

            result = geo_data['results'][0]
            lat = result['latitude']
            lon = result['longitude']
            place_name = result['name']
            country = result.get('country', '')

            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            weather_response = requests.get(weather_url, timeout=5)
            weather_data = weather_response.json()

            current = weather_data['current_weather']
            temp = current['temperature']
            windspeed = current['windspeed']

            if temp > 30:
                temp_emoji = "🔥"
            elif temp > 20:
                temp_emoji = "☀️"
            elif temp > 10:
                temp_emoji = "🌤️"
            elif temp > 0:
                temp_emoji = "☁️"
            else:
                temp_emoji = "❄️"

            location_display = place_name
            if country and country != place_name:
                location_display += f", {country}"

            return f"{temp_emoji} {location_display}: {temp}°C (רוח {windspeed} קמ\"ש)"

        except Exception as e:
            logger.error(f"Weather error: {e}")
            return f"בעיה בקבלת מזג אוויר עבור {location} 🌍"

# === SECURITY ===
class SecurityService:
    def __init__(self):
        self.rate_limits = {}

    def is_rate_limited(self, user_id: str) -> bool:
        now = time.time()
        user_requests = self.rate_limits.get(user_id, [])
        recent_requests = [ts for ts in user_requests if now - ts < 60]
        self.rate_limits[user_id] = recent_requests
        if len(recent_requests) >= config.MAX_REQUESTS_PER_MINUTE:
            return True
        self.rate_limits[user_id].append(now)
        return False

# === USER SERVICE ===
class UserService:
    def get_or_create_user(self, telegram_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(telegram_data.get('id'))
        if user_id not in user_data:
            user_data[user_id] = {
                'telegram_id': user_id,
                'first_name': telegram_data.get('first_name', ''),
                'last_name': telegram_data.get('last_name', ''),
                'username': telegram_data.get('username', ''),
                'language_code': telegram_data.get('language_code', 'he'),
                'total_messages': 0,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'is_active': True
            }
            save_data()
            logger.info(f"Created new user: {user_id}")
        return user_data[user_id]

    def update_user_activity(self, user_id: str):
        if user_id in user_data:
            user_data[user_id]['last_activity'] = datetime.now().isoformat()
            user_data[user_id]['total_messages'] += 1
            save_data()

    def get_user_context(self, user_id: str) -> str:
        user = user_data.get(user_id, {})
        user_memories = memories.get(user_id, [])
        if user_memories:
            context = f"דברים שהמשתמש סיפר: {', '.join(user_memories[-3:])}"
        else:
            context = ""
        return context

    def add_memory(self, user_id: str, content: str):
        if user_id not in memories:
            memories[user_id] = []
        memories[user_id].append(content)
        if len(memories[user_id]) > 10:
            memories[user_id] = memories[user_id][-10:]
        save_data()

# === TELEGRAM BOT ===
class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        logger.info("Telegram bot initialized")

    def send_message(self, chat_id: int, text: str, parse_mode: str = None):
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text[:4096],
            }
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            if result.get("ok"):
                logger.debug(f"Message sent to chat {chat_id}")
                time.sleep(0.5)
            else:
                logger.error(f"Failed to send message: {result}")
            return result
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return {"ok": False, "error": str(e)}

    def process_update(self, update: Dict[str, Any]):
        try:
            if "message" not in update:
                return
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_data_tg = message.get("from", {})
            text = message.get("text", "")
            logger.info(f"Message from {user_data_tg.get('first_name', 'Unknown')}: {text}")
            if security.is_rate_limited(str(user_data_tg.get("id", 0))):
                self.send_message(chat_id, "יותר מדי בקשות. חכה דקה ונסה שוב.")
                return
            user = user_service.get_or_create_user(user_data_tg)
            user_service.update_user_activity(user['telegram_id'])
            if text.startswith('/'):
                self._handle_command(chat_id, text, user)
            else:
                self._handle_message(chat_id, text, user)
        except Exception as e:
            logger.error(f"Process update error: {e}")

    def _handle_command(self, chat_id: int, command: str, user: Dict[str, Any]):
        cmd = command.split()[0].lower()
        if cmd == "/start":
            response = f"היי {user['first_name']}! אני מאיה 🤖"
        elif cmd == "/help":
            response = """פקודות זמינות:
/help - עזרה  
/memory - זיכרון
/weather [מקום] - מזג אוויר
/stats - סטטיסטיקות
/forget - מחק זיכרון

אבל אתה לא צריך פקודות! פשוט כתוב לי מה שאתה רוצה 💬"""
        elif cmd == "/memory":
            context = user_service.get_user_context(user['telegram_id'])
            response = f"🧠 מה שאני זוכרת:\n{context}" if context else "אין זיכרונות עדיין"
        elif cmd == "/weather":
            location = command.replace("/weather", "").strip() or "תל אביב"
            response = weather_service.get_weather_anywhere(location)
        elif cmd == "/stats":
            total_users = len(user_data)
            response = f"📊 {total_users} משתמשים רשומים"
        elif cmd == "/forget":
            user_id = user['telegram_id']
            if user_id in memories:
                del memories[user_id]
                save_data()
            response = "🗑️ מחקתי הכל"
        else:
            response = "לא מכירה את הפקודה. כתוב /help"
        self.send_message(chat_id, response)

    def _handle_message(self, chat_id: int, text: str, user: Dict[str, Any]):
        user_id = user['telegram_id']
        personal_keywords = ["קוראים לי", "אני עובד", "אני גר", "אני אוהב", "שמי"]
        if any(phrase in text.lower() for phrase in personal_keywords):
            user_service.add_memory(user_id, text)
        context = user_service.get_user_context(user_id)
        response = ai_service.generate_response(user_id, text, context)
        if user_id not in conversations:
            conversations[user_id] = []
        conversations[user_id].append({
            'message': text,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        if len(conversations[user_id]) > 20:
            conversations[user_id] = conversations[user_id][-20:]
        save_data()
        self.send_message(chat_id, response)

# === SERVICES INITIALIZATION ===
security = SecurityService()
user_service = UserService()
weather_service = GlobalWeatherService()
ai_service = ClaudeStyleAI()
bot = TelegramBot()

# === FLASK ROUTES ===
@app.route("/", methods=["GET"])
def health_check():
    try:
        usage_stats = ai_service.get_usage_stats()
        return jsonify({
            "status": "healthy",
            "service": "Maya 3.0 - Claude-like Assistant",
            "version": "3.0.1-stable-services",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": config.ENVIRONMENT,
            "users": len(user_data),
            "ai_model": config.GEMINI_MODEL,
            "services_initialized": {
                "security": security is not None,
                "user_service": user_service is not None,
                "weather_service": weather_service is not None,
                "ai_service": ai_service is not None,
                "bot": bot is not None
            },
            "features": [
                "claude_intelligence_engine",
                "built_in_knowledge_base",
                "contextual_understanding",
                "short_natural_responses",
                "no_automatic_greetings",
                "stable_service_initialization"
            ],
            "gemini_usage": usage_stats
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "service": "Maya 3.0",
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        if not update:
            return "No data", 400
        bot.process_update(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route("/stats", methods=["GET"])
def api_stats():
    try:
        usage_stats = ai_service.get_usage_stats()
        stats = {
            "total_users": len(user_data),
            "active_users": sum(1 for u in user_data.values() if u.get('is_active', True)),
            "total_conversations": sum(len(conversations.get(uid, [])) for uid in conversations),
            "total_memories": sum(len(memories.get(uid, [])) for uid in memories),
            "version": "3.0.1-stable-services",
            "services_status": {
                "all_initialized": all([security, user_service, weather_service, ai_service, bot]),
                "security": security is not None,
                "user_service": user_service is not None,
                "weather_service": weather_service is not None,
                "ai_service": ai_service is not None,
                "bot": bot is not None
            },
            "features": {
                "claude_intelligence_engine": True,
                "built_in_knowledge": True,
                "contextual_understanding": True,
                "natural_responses": True,
                "weather_service": True,
                "memory_system": True,
                "stable_initialization": True
            },
            "gemini_usage": usage_stats
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": "Stats unavailable", "details": str(e)}), 500

@app.route("/test_intelligence", methods=["POST"])
def test_intelligence():
    try:
        data = request.get_json()
        message = data.get('message', '')
        if not message:
            return jsonify({"error": "No message provided"}), 400
        intelligence_engine = ClaudeIntelligenceEngine()
        result = intelligence_engine.analyze_and_respond(message)
        return jsonify({
            "input_message": message,
            "analysis_result": result,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Intelligence test error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/usage", methods=["GET"])
def api_usage():
    try:
        usage_stats = ai_service.get_usage_stats()
        return jsonify(usage_stats)
    except Exception as e:
        logger.error(f"Usage stats error: {e}")
        return jsonify({"error": "Usage stats unavailable", "details": str(e)}), 500

@app.route("/set_webhook", methods=["POST"])
def set_webhook():
    try:
        webhook_url = config.WEBHOOK_URL
        if not webhook_url:
            return jsonify({"error": "WEBHOOK_URL not configured"}), 400
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
        data = {"url": webhook_url}
        logger.info(f"Setting webhook to: {webhook_url}")
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result.get("ok"):
            logger.info(f"Webhook set successfully: {webhook_url}")
            return jsonify({"success": True, "webhook_url": webhook_url})
        else:
            logger.error(f"Failed to set webhook: {result}")
            return jsonify({"error": "Failed to set webhook"}), 500
    except Exception as e:
        logger.error(f"Set webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

def set_webhook_on_startup():
    if config.ENVIRONMENT == "production" and config.WEBHOOK_URL:
        try:
            url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
            data = {"url": config.WEBHOOK_URL}
            logger.info(f"Setting webhook on startup: {config.WEBHOOK_URL}")
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            if result.get("ok"):
                logger.info(f"Webhook set on startup: {config.WEBHOOK_URL}")
            else:
                logger.error(f"Failed to set webhook on startup: {result}")
        except Exception as e:
            logger.error(f"Webhook setup error on startup: {e}")
    else:
        logger.info("Webhook not set - missing WEBHOOK_URL or not in production")

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Starting Maya 3.0 - Stable Services")
    logger.info("=" * 50)
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"AI Model: {config.GEMINI_MODEL}")
    try:
        usage_stats = ai_service.get_usage_stats()
        logger.info(f"Gemini usage today: {usage_stats['daily_requests']}/{usage_stats['daily_limit']} ({usage_stats['percentage_used_today']}%)")
        test_result = ai_service.intelligence_engine.analyze_and_respond("מתי המונדיאל הבא?")
        logger.info(f"Intelligence engine test: {test_result['type']} - {bool(test_result.get('response'))}")
    except Exception as e:
        logger.error(f"Service tests failed: {e}")
    set_webhook_on_startup()
    logger.info("🚀 Maya 3.0 ready to serve!")
    logger.info("=" * 50)
    app.run(
        host="0.0.0.0",
        port=config.PORT,
        debug=config.DEBUG
    )
