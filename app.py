import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests
import pytz
from typing import Dict, Any, Optional
import time
import collections # For deque

# Third-party imports
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold # For safety settings

# Assuming 'config' is a separate file like config.py
import config

# === ENHANCED LOGGING SETUP ===
# We'll also capture recent logs in memory for /diagnostic endpoint
MAX_DIAG_LOGS = 50
diagnostic_logs = collections.deque(maxlen=MAX_DIAG_LOGS)

class DiagnosticLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': self.format(record)
        }
        diagnostic_logs.append(log_entry)

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# Add our custom handler to the root logger or specific loggers
logging.getLogger().addHandler(DiagnosticLogHandler())


# === FLASK APP SETUP ===

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# === DATA STORAGE (JSON) ===

DATA_FILE = "maya_data.json"
GEMINI_USAGE_FILE = "gemini_usage.json"
user_data = {}
conversations = {}
memories = {}

def load_data():
    """Load data from JSON file"""
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
    """Save data to JSON file"""
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

# Load data on startup
load_data()

# === GEMINI API TRACKER ===

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
                logger.debug(f"Loaded usage: {self.usage_data.get('daily_requests', 0)} requests today")
            except Exception as e: # Catch specific parsing errors
                logger.warning(f"Could not load usage data from {self.usage_file}: {e}. Initializing fresh.")
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
            data = self.usage_data.copy() # Make a copy to avoid modifying original during dump
            # Convert datetime objects to string if any managed to creep in (should be isoformat already)
            data['minute_requests'] = [str(dt) for dt in data['minute_requests']]
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
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
        # Ensure items in minute_requests are datetime objects for comparison
        # (they should be isoformat strings if saved/loaded correctly)
        self.usage_data['minute_requests'] = [
            req_time for req_time in self.usage_data['minute_requests']
            if datetime.fromisoformat(req_time) > minute_ago # Assuming isoformat
        ]

        if self.usage_data['daily_requests'] >= self.daily_limit:
            logger.warning(f"Daily limit reached: {self.usage_data['daily_requests']}/{self.daily_limit}")
            return False, f"הגעת למגבלה היומית ({self.daily_limit})"
        if len(self.usage_data['minute_requests']) >= self.minute_limit:
            logger.warning(f"Minute limit reached: {len(self.usage_data['minute_requests'])}/{self.minute_limit}")
            return False, f"יותר מדי בקשות בדקה ({self.minute_limit})"

        remaining = self.daily_limit - self.usage_data['daily_requests']
        logger.debug(f"Usage check OK. Daily: {self.usage_data['daily_requests']}/{self.daily_limit}. Minute: {len(self.usage_data['minute_requests'])}/{self.minute_limit}")
        return True, f"OK (נותרו: {remaining})"

    def record_request(self, tokens_used=0):
        now = datetime.now()
        self.usage_data['daily_requests'] += 1
        self.usage_data['total_requests_ever'] += 1
        self.usage_data['minute_requests'].append(now.isoformat())
        self.usage_data['total_tokens'] += tokens_used
        self.save_usage_data()
        logger.info(f"Recorded Gemini API request. Daily: {self.usage_data['daily_requests']}/{self.daily_limit}, Tokens: {tokens_used}")

    def get_usage_stats(self):
        # Refresh minute_requests on access for accuracy
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        self.usage_data['minute_requests'] = [
            req_time for req_time in self.usage_data['minute_requests']
            if datetime.fromisoformat(req_time) > minute_ago
        ]

        return {
            'daily_requests': self.usage_data['daily_requests'],
            'daily_limit': self.daily_limit,
            'daily_remaining': self.daily_limit - self.usage_data['daily_requests'],
            'minute_requests_count': len(self.usage_data['minute_requests']),
            'minute_limit': self.minute_limit,
            'total_tokens': self.usage_data['total_tokens'],
            'total_requests_ever': self.usage_data['total_requests_ever'],
            'percentage_used_today': round((self.usage_data['daily_requests'] / self.daily_limit) * 100, 1) if self.daily_limit > 0 else 0
        }

# === SECURITY & RATE LIMITING ===

class SecurityService:
    def __init__(self):
        self.rate_limits = {}

    def is_rate_limited(self, user_id: str) -> bool:
        now = time.time()
        user_requests = self.rate_limits.get(user_id, [])
        recent_requests = [ts for ts in user_requests if now - ts < 60]
        self.rate_limits[user_id] = recent_requests

        if len(recent_requests) >= config.MAX_REQUESTS_PER_MINUTE:
            logger.warning(f"Rate limit exceeded for user {user_id}. {len(recent_requests)} requests in last minute.")
            return True

        self.rate_limits[user_id].append(now)
        logger.debug(f"User {user_id} not rate limited. Requests in last minute: {len(self.rate_limits[user_id])}")
        return False

security = SecurityService()

# === GLOBAL WEATHER SERVICE ===

class GlobalWeatherService:
    """Global weather service for any location worldwide"""

    def extract_location(self, text: str) -> str:
        """Extract location from text"""
        text = text.replace("מזג אוויר", "").replace("טמפרטורה", "")
        text = text.replace("ב", "").replace("של", "").replace("את", "")
        text = text.strip()

        if not text or len(text) < 2:
            return "תל אביב"

        return text

    def get_weather_anywhere(self, location: str) -> str:
        """Get weather for any location worldwide"""
        try:
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=he&format=json"
            geo_response = requests.get(geocoding_url, timeout=5)
            geo_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            geo_data = geo_response.json()

            if not geo_data.get('results'):
                logger.warning(f"No geocoding results for location: {location}")
                return f"מצטערת, לא מצאתי את המקום '{location}'. נסה לכתוב בדרך אחרת 🌍"

            result = geo_data['results'][0]
            lat = result['latitude']
            lon = result['longitude']
            place_name = result['name']
            country = result.get('country', '')

            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            weather_response = requests.get(weather_url, timeout=5)
            weather_response.raise_for_status() # Raise HTTPError
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

            location_display = f"{place_name}"
            if country and country != place_name:
                location_display += f", {country}"

            result = f"{temp_emoji} מזג האוויר ב{location_display}:\n🌡️ {temp}°C\n💨 רוח: {windspeed} קמ\"ש"
            logger.debug(f"Weather fetched for {location_display}: {temp}°C")
            return result

        except requests.exceptions.RequestException as req_e:
            logger.error(f"Network/HTTP error fetching weather for {location}: {req_e}")
            return f"מצטערת, בעיה ברשת בקבלת מזג אוויר עבור {location}. נסה שוב! 🌍"
        except json.JSONDecodeError:
            logger.error(f"JSON decode error from weather API for {location}. Response: {geo_response.text if 'geo_response' in locals() else 'N/A'}")
            return f"מצטערת, בעיה בעיבוד התשובה ממזג האוויר עבור {location}. 🌍"
        except Exception as e:
            logger.error(f"Unexpected error in get_weather_anywhere for {location}: {e}", exc_info=True) # exc_info to get traceback
            return f"מצטערת, לא הצלחתי לקבל מזג אוויר עבור {location}. נסה שם מקום אחר 🌍"

weather_service = GlobalWeatherService()

# === WEB SEARCH SERVICE ===

class WebSearchService:
    """Web search service for real-time information like Claude"""

    def search_web(self, query: str) -> str:
        """Search the web for current information"""
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1&no_html=1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('AbstractText'):
                return data['AbstractText'][:400] + "..."
            elif data.get('Answer'):
                return data['Answer']
            elif data.get('Definition'):
                return data['Definition']
            elif data.get('RelatedTopics') and len(data['RelatedTopics']) > 0:
                topic = data['RelatedTopics'][0]
                if topic.get('Text'):
                    return topic['Text'][:300] + "..."
            else:
                return self._fallback_search(query)

        except requests.exceptions.RequestException as req_e:
            logger.error(f"Network/HTTP error during DuckDuckGo search for '{query}': {req_e}")
            return f"לא הצלחתי לחפש באינטרנט עבור '{query}'. בעיה ברשת. 🔍"
        except json.JSONDecodeError:
            logger.error(f"JSON decode error from DuckDuckGo for '{query}'. Response: {response.text if 'response' in locals() else 'N/A'}")
            return f"לא הצלחתי לחפש באינטרנט עבור '{query}'. בעיה בעיבוד התשובה. 🔍"
        except Exception as e:
            logger.error(f"Unexpected error in search_web for '{query}': {e}", exc_info=True)
            return f"לא הצלחתי לחפש באינטרנט עבור '{query}'. נסה שאלה אחרת 🔍"

    def _fallback_search(self, query: str) -> str:
        """Fallback search method using Wikipedia"""
        try:
            wiki_url = f"https://he.wikipedia.org/api/rest_v1/page/summary/{query}"
            response = requests.get(wiki_url, timeout=5)
            response.raise_for_status()

            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    return data['extract'][:350] + "..."

            wiki_url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
            response_en = requests.get(wiki_url_en, timeout=5)
            response_en.raise_for_status()

            if response_en.status_code == 200:
                data_en = response_en.json()
                if data_en.get('extract'):
                    return data_en['extract'][:350] + "...\n(מקור: ויקיפדיה באנגלית)"

            return f"לא מצאתי מידע מועיל על '{query}'. נסה לנסח אחרת 🤔"

        except requests.exceptions.RequestException as req_e:
            logger.error(f"Network/HTTP error during Wikipedia search for '{query}': {req_e}")
            return f"בעיה ברשת בחיפוש בויקיפדיה עבור '{query}' 😔"
        except json.JSONDecodeError:
            logger.error(f"JSON decode error from Wikipedia for '{query}'. Response: {response.text if 'response' in locals() else 'N/A'}")
            return f"בעיה בעיבוד התשובה מויקיפדיה עבור '{query}' 😔"
        except Exception as e:
            logger.error(f"Unexpected error in _fallback_search for '{query}': {e}", exc_info=True)
            return f"בעיה בחיפוש '{query}' 😔"

    def get_current_info(self, topic: str) -> str:
        """Get current information with Claude-like confidence"""
        if any(word in topic.lower() for word in ["מונדיאל", "world cup"]):
            return """המונדיאל הבא יתקיים ב-2026! 🏆

📍 איפה: שלוש מדינות יחד
- 🇺🇸 ארצות הברית (רוב המשחקים)
- 🇲🇽 מקסיקו
- 🇨🇦 קנדה

⚽ מה מיוחד:
- 48 נבחרות (במקום 32)
- 104 משחקים סה"כ
- המונדיאל הגדול ביותר בהיסטוריה!

🗓️ מתי: קיץ 2026 (התאריכים המדויקים יפורסמו השנה)"""

        elif any(word in topic.lower() for word in ["אולימפיאדה", "olympics"]):
            return """האולימפיאדה הבאה תהיה ב-2028! 🏅

📍 לוס אנג’לס, ארצות הברית
🗓️ יולי-אוגוסט 2028
🏟️ אולימפיאדת הקיץ השלישית בלוס אנג’לס"""

        else:
            try:
                search_result = self.search_web(topic)
                if len(search_result) > 50 and "לא מצאתי" not in search_result and "לא הצלחתי" not in search_result:
                    return search_result
                else:
                    return f"אין לי מידע עדכני מספק על '{topic}'. \nאוכל לעזור בנושא אחר? 🤔"
            except Exception as e:
                logger.error(f"Error in get_current_info for topic '{topic}': {e}", exc_info=True)
                return f"לא הצלחתי לחפש מידע על '{topic}' כרגע. \nנסה שאלה אחרת! 💭"

web_search_service = WebSearchService()

# === AI SERVICE ===

class AIService:
    def __init__(self):
        try:
            # Ensure API key is set before configuring
            if not config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set in config.py or environment variables.")

            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                config.GEMINI_MODEL,
                # Optional: Add safety settings to reduce blocked content
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            self.chat_sessions = {}
            self.system_instruction = self._get_system_instruction()
            self.tracker = GeminiTracker()
            logger.info(f"AI Service initialized with model: {config.GEMINI_MODEL}")

            stats = self.tracker.get_usage_stats()
            logger.info(f"Gemini API Usage today: {stats['daily_requests']}/{stats['daily_limit']} ({stats['percentage_used_today']}%)")

        except Exception as e:
            logger.error(f"AI Service initialization failed: {e}", exc_info=True) # Added exc_info=True for traceback
            raise

    def _get_system_instruction(self) -> str:
        # Refined system instruction
        return """
    את מאיה, עוזרת AI חכמה ומועילה. את מדברת בעברית בלבד (אלא אם התבקשת ספציפית לדבר בשפה אחרת).
    תפקידך הוא להיות מזכירה אישית וירטואלית, ידידותית, יעילה ומקצועית, המסוגלת לתת מידע מדויק, לבצע חיפושים, ולנהל שיחות באופן טבעי.

    עקרונות התנהגות:
    1. **עזרה ותועלת**: תמיד תנסי לעזור למשתמש ולספק מידע רלוונטי ומדויק.
    2. **שקיפות ויושרה**: אם אינך יודעת משהו, תודי בכנות ותציעי לחפש מידע (אם רלוונטי) או לנסות שאלה אחרת.
    3. **ידידותית ומקצועית**: שמרי על טון חברותי, תומך ומכבד.
    4. **בהירות ותמציתיות**: תני תשובות ברורות, מובנות ולעניין.
    5. **התאמה אישית**: זכרי הקשר ופרטים שחשובים למשתמש (שנשמרו ב"זיכרונות").
    6. **שימוש בכלים**: השתמשי ביכולות שלך (חיפוש, מזג אוויר) במידת הצורך כדי לספק את התשובה הטובה ביותר.

    יכולות מיוחדות:
    - **חיפוש מידע באינטרנט**: עבור שאלות הדורשות מידע עדכני או ספציפי (למשל: "מה מזג האוויר בתל אביב?", "מי נשיא ארה"ב?", "מה חדש בחדשות?").
    - **מידע עדכני מובנה**: על אירועים גדולים וקבועים כמו מונדיאל או אולימפיאדה (מידע מתוכנן מראש).
    - **זיכרון**: שמירת פרטים מהשיחה כדי לספק הקשר טוב יותר בתשובות עתידיות.
    - **שיחה רגילה**: ניהול שיחות כלליות, עזרה בכתיבה, רעיונות וכו'.

    דגש: נסי למנוע תשובות גנריות של "אני מודל שפה גדול", אלא התנהגי כעוזרת וירטואלית ממשית.
    """

    def generate_response(self, user_id: str, message: str, context: str = "") -> str:
        logger.debug(f"Entering generate_response for user {user_id}. Message: {message[:100]}")
        try:
            can_request, status_message = self.tracker.can_make_request()
            if not can_request:
                logger.warning(f"Gemini API request blocked for user {user_id} due to rate limits: {status_message}")
                return f"מצטערת, {status_message}\n\nנסה שוב מאוחר יותר! 😊"

            # Check if API key is loaded before proceeding with actual API calls
            if not config.GEMINI_API_KEY or not self.model:
                logger.error(f"Gemini API key is missing or model not initialized for user {user_id}.")
                return "אופס, בעיה בתצורה של שירות ה-AI. אנא דווח למפתח." # More specific error for debug

            # --- Simplified logic for _deep_analyze_question and _determine_response_strategy ---
            # Instead of separate steps, let's consolidate for better flow control for diagnostic.
            # The actual logic inside these helper functions should still guide the decision.

            message_lower = message.lower()
            response_content = ""
            is_handled_by_tool = False

            if any(word in message_lower for word in ["מזג אוויר", "טמפרטורה", "חם", "קר", "מעלות", "weather"]):
                location = weather_service.extract_location(message)
                response_content = weather_service.get_weather_anywhere(location)
                is_handled_by_tool = True
                logger.info(f"Handled weather query for {location}")

            elif "שעה" in message_lower or "זמן" in message_lower:
                israel_tz = pytz.timezone("Asia/Jerusalem")
                now = datetime.now(israel_tz)
                response_content = f"🕐 השעה בישראל: {now.strftime('%H:%M')}\n📅 {now.strftime('%A, %d %B %Y')}"
                is_handled_by_tool = True
                logger.info("Handled time query")

            elif any(word in message_lower for word in ["מונדיאל", "world cup", "אולימפיאדה", "olympics", "מי זה", "מה זה", "חיפוש"]):
                response_content = web_search_service.get_current_info(message) # This handles both pre-canned and web search
                is_handled_by_tool = True
                logger.info(f"Handled web/pre-canned info query for: {message[:50]}")

            # If not handled by specific tools, use conversational AI
            if not is_handled_by_tool:
                response_content = self._generate_conversational_response(user_id, message, context)
                logger.info(f"Generated conversational response for user {user_id}")

            logger.debug(f"Leaving generate_response for user {user_id}. Response: {response_content[:100]}")
            return response_content

        except Exception as e:
            logger.error(f"Critical error in generate_response for user {user_id} with message '{message[:100]}': {e}", exc_info=True)
            if config.DEBUG:
                # Return detailed error to user ONLY IN DEBUG MODE for security
                return f"אופס, שגיאה פנימית חמורה: {type(e).__name__}: {e}\n\nנא דווח למפתח! 🐛"
            else:
                return "משהו השתבש בצד שלי, בוא ננסה שוב! ✨"


    def _generate_conversational_response(self, user_id: str, message: str, context: str, retry_count=0) -> str:
        """Generates a conversational response using the Gemini API."""
        logger.debug(f"Calling _generate_conversational_response for user {user_id}, retry {retry_count}")
        try:
            # Get existing chat session or create a new one
            if user_id not in self.chat_sessions:
                logger.info(f"Starting new chat session for user {user_id}")
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
            chat = self.chat_sessions[user_id]

            # Construct the prompt for Gemini
            full_prompt = f"""
            {self.system_instruction}

            --- שיחה אחרונה ---
            הודעת משתמש: {message}
            הקשר נוסף (מזיכרונות המערכת): {context}

            תגובה:
            """
            logger.debug(f"Sending prompt to Gemini for user {user_id}: {full_prompt[:500]}...")

            response = chat.send_message(full_prompt) # This is the main API call

            # Attempt to extract text, handle potential errors from Gemini
            response_text = ""
            if response and response.text:
                response_text = response.text
                logger.info(f"Received response from Gemini for user {user_id}. Text length: {len(response_text)}")
                # Consider adding token count if available from Gemini response for accurate tracking
                # For Gemini, response.usage_metadata might provide token counts
                tokens_used = 0
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    if hasattr(response.usage_metadata, 'total_token_count'):
                        tokens_used = response.usage_metadata.total_token_count
                self.tracker.record_request(tokens_used=tokens_used)
            elif response and response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name
                logger.warning(f"Gemini API blocked prompt for user {user_id}. Reason: {block_reason}. Message: {message[:100]}")
                return f"מצטערת, התוכן ששלחת נחסם על ידי מערכות הבטיחות של ה-AI ({block_reason}). נסה/נסי לנסח מחדש? 🙏"
            else:
                logger.warning(f"Gemini API returned no text or unexpected response for user {user_id}. Response: {response}")
                if retry_count < 1: # Basic retry mechanism
                    logger.info(f"Retrying Gemini call for user {user_id}...")
                    time.sleep(0.5) # Wait a bit before retrying
                    return self._generate_conversational_response(user_id, message, context, retry_count + 1)
                else:
                    return "אופס, לא קיבלתי תגובה טובה מה-AI. נסה/נסי שוב מאוחר יותר. 😔"

            return response_text

        except Exception as e:
            logger.error(f"Error during Gemini API call for user {user_id} with message '{message[:100]}': {e}", exc_info=True)
            # Re-raise to be caught by the higher-level generate_response for common error handling
            raise


    def get_usage_stats(self):
        return self.tracker.get_usage_stats()

# Initialize AI service AFTER other services it depends on (like web_search_service, weather_service)
ai_service = AIService() # Initialize after weather_service and web_search_service

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
            logger.info(f"Created new user: {user_id} ({telegram_data.get('first_name', 'Unknown')})")

        return user_data[user_id]

    def update_user_activity(self, user_id: str):
        if user_id in user_data:
            user_data[user_id]['last_activity'] = datetime.now().isoformat()
            user_data[user_id]['total_messages'] += 1
            save_data()
            logger.debug(f"Updated activity for user {user_id}")

    def get_user_context(self, user_id: str) -> str:
        user = user_data.get(user_id, {})
        user_memories = memories.get(user_id, [])

        context = f"""
    משתמש: {user.get('first_name', 'חבר/ה')} (ID: {user.get('telegram_id', 'Unknown')})
    סה"כ הודעות: {user.get('total_messages', 0)}
    זיכרונות קשורים (עד 5 אחרונים): {', '.join(user_memories[-5:]) if user_memories else 'אין זיכרונות'}
    """

        return context

    def add_memory(self, user_id: str, content: str):
        if user_id not in memories:
            memories[user_id] = []

        memories[user_id].append(content)

        if len(memories[user_id]) > 10:
            memories[user_id] = memories[user_id][-10:]

        save_data()
        logger.debug(f"Added memory for user {user_id}: {content[:50]}...")

user_service = UserService()

# === TELEGRAM BOT LOGIC ===

class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        logger.info(f"Telegram bot initialized with token: {self.token[:10]}...")

    def send_message(self, chat_id: int, text: str, parse_mode: str = None):
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text[:4096],
            }
            if parse_mode:
                data["parse_mode"] = parse_mode

            logger.debug(f"Sending message to chat {chat_id}: {text[:50]}...")
            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("ok"):
                logger.debug(f"Message sent successfully to chat {chat_id}")
            else:
                logger.error(f"Failed to send message to chat {chat_id}: {result.get('description', result)}")
                # If Telegram reports error, it's often due to message content (e.g. invalid markdown) or user block
                if "blocked by the user" in result.get('description', '').lower():
                    logger.warning(f"Bot blocked by user {chat_id}")

            return result

        except requests.exceptions.RequestException as req_e:
            logger.error(f"Network/HTTP error sending message to {chat_id}: {req_e}")
            return {"ok": False, "error": str(req_e)}
        except json.JSONDecodeError:
            logger.error(f"JSON decode error from Telegram API sending message to {chat_id}. Response: {response.text if 'response' in locals() else 'N/A'}")
            return {"ok": False, "error": "Invalid JSON response from Telegram"}
        except Exception as e:
            logger.error(f"Unexpected error sending message to {chat_id}: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}

    def process_update(self, update: Dict[str, Any]):
        try:
            logger.debug(f"Processing update: {json.dumps(update, indent=2)}")

            if "message" not in update:
                logger.debug("No message in update, skipping")
                return

            message = update["message"]
            chat_id = message["chat"]["id"]
            user_data_tg = message.get("from", {})
            text = message.get("text", "")
            user_id_str = str(user_data_tg.get("id", 0))

            logger.info(f"Received message from {user_data_tg.get('first_name', 'Unknown')} (ID: {user_id_str}): {text}")

            if security.is_rate_limited(user_id_str):
                self.send_message(chat_id, "⚠️ יותר מדי בקשות. המתן דקה ונסה שוב.")
                return

            user = user_service.get_or_create_user(user_data_tg)
            user_service.update_user_activity(user['telegram_id'])

            if text.startswith('/'):
                logger.debug(f"Processing command: {text}")
                self._handle_command(chat_id, text, user)
            else:
                logger.debug(f"Processing regular message: {text}")
                self._handle_message(chat_id, text, user)

        except Exception as e:
            logger.error(f"Process update error: {e}", exc_info=True)
            # Send a generic error message to the user if an unhandled error occurs during update processing
            try:
                self.send_message(chat_id, "אופס, נתקלתי בשגיאה כללית בעיבוד הודעתך. נא דווח/י למפתח.")
            except Exception as send_e:
                logger.error(f"Failed to send generic error message to user {chat_id}: {send_e}")


    def _handle_command(self, chat_id: int, command: str, user: Dict[str, Any]):
        cmd = command.split()[0].lower()
        logger.debug(f"Handling command: {cmd}")
        response = "" # Initialize response

        try:
            if cmd == "/start":
                response = f"🌟 שלום {user['first_name']}! אני מאיה, המזכירה שלך!\n\nאיך אוכל לעזור לך היום? 😊"

            elif cmd == "/help":
                response = """
    🤖 מאיה - המזכירה שלך

    פקודות:
    /start - התחלה
    /help - עזרה
    /memory - מה שאני זוכרת
    /weather [מיקום] - מזג אוויר
    /stats - סטטיסטיקות
    /usage - שימוש ב-AI API
    /forget - מחק זיכרון

    פשוט כתוב לי מה שאתה צריך! 💪
    """
            elif cmd == "/memory":
                context = user_service.get_user_context(user['telegram_id'])
                response = f"🧠 הנה מה שאני זוכרת עליך:\n\n{context}"

            elif cmd == "/weather":
                location_text = command.replace("/weather", "").strip()
                location = location_text if location_text else "תל אביב"
                response = weather_service.get_weather_anywhere(location)

            elif cmd == "/stats":
                total_users = len(user_data)
                total_conversations = sum(len(conversations.get(uid, [])) for uid in conversations)
                response = f"📊 סטטיסטיקות:\n👥 משתמשים: {total_users}\n💬 שיחות: {total_conversations}\n🤖 אני פעילה!"

            elif cmd == "/usage":
                try:
                    usage_stats = ai_service.get_usage_stats()
                    response = f"""📊 שימוש ב-Gemini API היום:

    🔢 בקשות: {usage_stats['daily_requests']}/{usage_stats['daily_limit']} ({usage_stats['percentage_used_today']}%)
    🎯 סה"כ בקשות: {usage_stats['total_requests_ever']}
    🪙 סה"כ טוקנים: {usage_stats['total_tokens']:,}

    💡 נותרו היום: {usage_stats['daily_remaining']} בקשות"""
                except Exception as e:
                    response = f"❌ שגיאה בקבלת נתוני שימוש: {e}"

            elif cmd == "/forget":
                user_id = user['telegram_id']
                if user_id in memories:
                    del memories[user_id]
                    logger.info(f"Forgot memories for user {user_id}")
                if user_id in conversations:
                    del conversations[user_id]
                    logger.info(f"Forgot conversations for user {user_id}")
                save_data()
                response = "🗑️ מחקתי הכל! נתחיל מחדש."

            else:
                response = "❓ לא מכירה את הפקודה הזו. כתוב /help לעזרה."

        except Exception as e:
            logger.error(f"Error handling command '{command}' for user {user['telegram_id']}: {e}", exc_info=True)
            response = "אופס, שגיאה בעיבוד הפקודה. נסה/נסי שוב."

        logger.debug(f"Command response: {response[:50]}...")
        self.send_message(chat_id, response)

    def _handle_message(self, chat_id: int, text: str, user: Dict[str, Any]):
        user_id = user['telegram_id']
        response = "" # Initialize response

        try:
            # The logic for choosing AI vs. tools is now primarily in AIService.generate_response
            # The AI service should decide if it needs to use external tools or respond conversationally.
            # So, we just pass the message and context to the AI service.
            context = user_service.get_user_context(user_id)
            response = ai_service.generate_response(user_id, text, context)

            # Store conversation history
            if user_id not in conversations:
                conversations[user_id] = []
            conversations[user_id].append({
                'message': text,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })

            # Trim conversation history
            if len(conversations[user_id]) > 20:
                conversations[user_id] = conversations[user_id][-20:]

            # Save data after AI response and history update
            save_data()

        except Exception as e:
            logger.error(f"Error handling message '{text[:100]}' for user {user_id}: {e}", exc_info=True)
            if config.DEBUG:
                response = f"אופס, שגיאה פנימית בהודעה: {type(e).__name__}: {e}"
            else:
                response = "משהו השתבש בצד שלי, בוא ננסה שוב! ✨"

        logger.debug(f"Final message response: {response[:50]}...")
        self.send_message(chat_id, response)

bot = TelegramBot()

# === FLASK ROUTES ===

@app.route("/", methods=["GET"])
def health_check():
    try:
        usage_stats = ai_service.get_usage_stats()
        return jsonify({
            "status": "healthy",
            "service": "Maya Secretary Bot - Gemini", # Changed for clarity
            "version": "2.2.0-diagnostic-ready", # Updated version for diagnostics
            "timestamp": datetime.utcnow().isoformat() + "Z", # UTC time, Z for Zulu time
            "environment": config.ENVIRONMENT,
            "users": len(user_data),
            "storage": "JSON",
            "ai_model": config.GEMINI_MODEL,
            "webhook_url": config.WEBHOOK_URL,
            "gemini_usage": {
                "daily_requests": usage_stats['daily_requests'],
                "daily_limit": usage_stats['daily_limit'],
                "percentage_used": usage_stats['percentage_used_today']
            }
        })
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        logger.info("Webhook called")
        update = request.get_json()

        if not update:
            logger.warning("Empty webhook request")
            return "No data", 400

        logger.debug(f"Webhook data: {json.dumps(update, indent=2)}")
        bot.process_update(update)

        logger.info("Webhook processed successfully")
        return "OK", 200

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
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
            "bot_status": "active",
            "storage_type": "JSON",
            "ai_model": config.GEMINI_MODEL,
            "webhook_url": config.WEBHOOK_URL,
            "gemini_usage": usage_stats
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        return jsonify({"error": "Stats unavailable"}), 500

@app.route("/usage", methods=["GET"])
def api_usage():
    try:
        usage_stats = ai_service.get_usage_stats()
        return jsonify(usage_stats)
    except Exception as e:
        logger.error(f"Usage stats error: {e}", exc_info=True)
        return jsonify({"error": "Usage stats unavailable"}), 500

@app.route("/set_webhook", methods=["POST"])
def set_webhook():
    try:
        webhook_url = config.WEBHOOK_URL
        if not webhook_url:
            return jsonify({"error": "WEBHOOK_URL not configured"}), 400
        if not config.TELEGRAM_TOKEN:
             return jsonify({"error": "TELEGRAM_TOKEN not configured"}), 400

        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
        data = {"url": webhook_url}

        logger.info(f"Attempting to set webhook to: {webhook_url}")
        response = requests.post(url, json=data, timeout=10)
        result = response.json()

        if result.get("ok"):
            logger.info(f"Webhook set successfully: {webhook_url}")
            return jsonify({"success": True, "webhook_url": webhook_url})
        else:
            logger.error(f"Failed to set webhook. Telegram API response: {result.get('description', result)}")
            return jsonify({"error": "Failed to set webhook", "telegram_response": result}), 500

    except requests.exceptions.RequestException as req_e:
        logger.error(f"Network/HTTP error setting webhook: {req_e}", exc_info=True)
        return jsonify({"error": f"Network error setting webhook: {req_e}"}), 500
    except Exception as e:
        logger.error(f"Set webhook error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/diagnostic", methods=["GET"])
def diagnostic_info():
    """Provides detailed diagnostic information about the bot's state."""
    if not config.DEBUG:
        return jsonify({"error": "Diagnostic endpoint is only available in DEBUG mode."}), 403

    try:
        gemini_api_key_set = bool(config.GEMINI_API_KEY)
        telegram_token_set = bool(config.TELEGRAM_TOKEN)
        secret_key_set = bool(config.SECRET_KEY)

        usage_stats = ai_service.get_usage_stats()

        diagnostic_report = {
            "service_status": "OK",
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "version": "2.2.0-diagnostic-ready",
            "environment": config.ENVIRONMENT,
            "debug_mode": config.DEBUG,
            "core_config_presence": {
                "TELEGRAM_TOKEN_set": telegram_token_set,
                "GEMINI_API_KEY_set": gemini_api_key_set,
                "WEBHOOK_URL": config.WEBHOOK_URL, # Display URL for check
                "FLASK_SECRET_KEY_set": secret_key_set
            },
            "data_summary": {
                "users_count": len(user_data),
                "conversations_count": sum(len(conv) for conv in conversations.values()),
                "memories_count": sum(len(mem) for mem in memories.values()),
                "data_file_exists": os.path.exists(DATA_FILE),
                "gemini_usage_file_exists": os.path.exists(GEMINI_USAGE_FILE)
            },
            "ai_service_state": {
                "model_name": config.GEMINI_MODEL,
                "chat_sessions_count": len(ai_service.chat_sessions),
                "gemini_tracker_stats": usage_stats
            },
            "recent_logs": list(diagnostic_logs), # Convert deque to list for JSON serialization
            "last_save_time": user_data.get('last_updated', 'N/A') if user_data else 'N/A' # This will be from user_data's meta
        }
        return jsonify(diagnostic_report)

    except Exception as e:
        logger.critical(f"Error generating diagnostic report: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate diagnostic report", "details": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500

def set_webhook_on_startup():
    if config.ENVIRONMENT == "production" and config.WEBHOOK_URL and config.TELEGRAM_TOKEN:
        try:
            url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
            data = {"url": config.WEBHOOK_URL}

            logger.info(f"Attempting to set webhook on startup: {config.WEBHOOK_URL}")
            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("ok"):
                logger.info(f"Webhook set on startup: {config.WEBHOOK_URL}")
            else:
                logger.error(f"Failed to set webhook on startup. Telegram API response: {result.get('description', result)}")
        except requests.exceptions.RequestException as req_e:
            logger.error(f"Network/HTTP error setting webhook on startup: {req_e}", exc_info=True)
        except Exception as e:
            logger.error(f"Webhook setup error on startup: {e}", exc_info=True)
    else:
        logger.info("Webhook not set on startup - check WEBHOOK_URL, TELEGRAM_TOKEN, or ENVIRONMENT ('production')")

if __name__ == "__main__":
    logger.info("Starting Maya Secretary Bot in development mode...")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"Storage: JSON files")
    logger.info(f"AI Model: {config.GEMINI_MODEL}")

    try:
        usage_stats = ai_service.get_usage_stats()
        logger.info(f"Gemini API Usage today: {usage_stats['daily_requests']}/{usage_stats['daily_limit']} ({usage_stats['percentage_used_today']}%)")
    except Exception as e:
        logger.error(f"Could not get usage stats on startup: {e}", exc_info=True)

    set_webhook_on_startup() # Still call it, but it will log if conditions aren't met

    app.run(
        host="0.0.0.0",
        port=config.PORT,
        debug=config.DEBUG # Use config.DEBUG here
    )
else:
    logger.info("Maya Secretary Bot starting via WSGI...")
    set_webhook_on_startup()
