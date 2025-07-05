# -*- coding: utf-8 -*-
# === Maya Secretary Bot 3.1 - The ULTIMATE Secretary Upgrade ===
import os
import json
import re
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
import requests
import pytz
import google.generativeai as genai
# Assuming config.py exists and has necessary variables like TELEGRAM_TOKEN, GEMINI_API_KEY, etc.
# For demonstration, I'll define a dummy config if not provided.
try:
    from config import config
except ImportError:
    class Config:
        TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
        WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "YOUR_WEBHOOK_URL")
        PORT = int(os.environ.get("PORT", 5000))
        DEBUG = os.environ.get("DEBUG", "False").lower() in ('true', '1', 't')
        ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
        MAX_REQUESTS_PER_MINUTE = 20
        GEMINI_MODEL = "gemini-1.5-flash" # Or "gemini-pro"
    config = Config()
    logging.warning("config.py not found or imported. Using dummy config. Please create config.py for production!")


# === LOGGING ===
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY # Assuming config.SECRET_KEY exists

# === DATA STORAGE ===
DATA_FILE = "maya_data.json"
GEMINI_USAGE_FILE = "gemini_usage.json"
user_data = {}
conversations = {} # Stores chat history for each user
memories = {} # Stores learned user facts

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
        logger.error(f"Error loading data: {e}. Starting with empty data.", exc_info=True)
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
        logger.error(f"Error saving data: {e}", exc_info=True)

load_data()

# === REAL WEB SEARCH SERVICE (Upgraded for better intent) ===
class WebSearchService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MayaBot/3.1'})
    
    def sanitize_query(self, query: str) -> str:
        """Cleans and truncates the query before searching."""
        return re.sub(r'[^\w\sא-ת\-.,?]', '', query)[:200]
    
    def search_web(self, query: str) -> Dict[str, Any]:
        sanitized_query = self.sanitize_query(query)
        logger.info(f"🔍 Searching web for: '{sanitized_query}'")
        
        try:
            params = {'q': sanitized_query, 'format': 'json', 'no_html': '1'}
            response = self.session.get(
                "https://api.duckduckgo.com/",
                params=params,
                timeout=5
            )
            response.raise_for_status() # Raise an exception for bad status codes
            data = response.json()
            
            if data.get("AbstractText"):
                answer = data["AbstractText"]
                if len(answer) > 300: # Limit answer length
                    answer = answer[:297] + "..."
                return {
                    "success": True,
                    "answer": answer,
                    "source": "DuckDuckGo",
                    "url": data.get("AbstractURL", "")
                }
            
            # Fallback to a related topic search if AbstractText is empty
            if data.get("RelatedTopics"):
                for topic in data["RelatedTopics"]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        answer = topic["Text"]
                        if len(answer) > 200:
                            answer = answer[:197] + "..."
                        return {
                            "success": True,
                            "answer": answer,
                            "source": "DuckDuckGo Related",
                            "url": topic.get("FirstURL", "")
                        }
            
            return {"success": False, "answer": "לא מצאתי מידע רלוונטי."}
        except requests.exceptions.RequestException as e:
            logger.error(f"Web search request error for '{query}': {e}", exc_info=True)
            return {"success": False, "answer": "בעיה בחיבור לאינטרנט."}
        except Exception as e:
            logger.error(f"Web search unexpected error for '{query}': {e}", exc_info=True)
            return {"success": False, "answer": "משהו השתבש בחיפוש."}

# === SUPER WEATHER SERVICE (Robust Location Handling) ===
class SuperWeatherService:
    """שירות מזג אוויר מתקדם - עובד עם כל המדינות!"""
    
    def __init__(self):
        # Expanded country-to-city mapping for common queries in Hebrew/English
        self.country_to_city = {
            "ארגנטינה": "Buenos Aires", "ברזיל": "São Paulo", "צרפת": "Paris",
            "גרמניה": "Berlin", "איטליה": "Rome", "ספרד": "Madrid",
            "אנגליה": "London", "יפן": "Tokyo", "ישראל": "Tel Aviv",
            "argentina": "Buenos Aires", "brazil": "São Paulo", "france": "Paris",
            "germany": "Berlin", "italy": "Rome", "spain": "Madrid",
            "england": "London", "japan": "Tokyo", "israel": "Tel Aviv",
            "ארהב": "New York", "ארה\"ב": "New York", "usa": "New York"
        }
    
    def get_weather_anywhere(self, location: str) -> str:
        """קבלת מזג אוויר - עובד עם מדינות וערים!"""
        
        try:
            clean_location = self._clean_location_text(location)
            english_location = self._convert_to_english(clean_location)
            
            coords = self._get_coordinates(english_location)
            if not coords:
                # Provide a more specific error for unrecognized location
                return f"❌ לא מצאתי מקום בשם '{clean_location}'! אולי תנסה שם אחר? 🤔"
            
            weather_data = self._get_weather_data(coords["lat"], coords["lon"])
            if not weather_data:
                return f"❌ לא הצלחתי לקבל מזג אוויר עבור {coords.get('display_name', clean_location)}."
            
            temp = weather_data["temperature"]
            place_name = coords.get("display_name", clean_location)
            
            # Dynamic emoji based on temperature
            if temp > 35: emoji = "🔥"
            elif temp > 25: emoji = "☀️"
            elif temp > 15: emoji = "🌤️"
            elif temp > 5: emoji = "☁️"
            else: emoji = "❄️"
            
            return f"{emoji} {place_name}: {temp}°C"
            
        except Exception as e:
            logger.error(f"Weather error for '{location}': {e}", exc_info=True)
            return f"🌍 בעיה בקבלת מזג אוויר עבור {location}. תנסה שוב! 😊"
    
    def _clean_location_text(self, location: str) -> str:
        """ניקוי טקסט מיותר מהמיקום, כולל סימני פיסוק."""
        remove_words = [
            "מזג אוויר", "טמפרטורה", "מעלות", "מה ה", "מה", 
            "איך ה", "כמה ה", "ב", "של", "את", "עכשיו", "היום",
            "בבקשה", "תגידי", "תני לי"
        ]
        
        clean_text = location.lower()
        for word in remove_words:
            clean_text = re.sub(r'\b' + re.escape(word) + r'\b', '', clean_text)
        
        # Remove extra spaces and punctuation at start/end
        clean_text = re.sub(r'[^א-ת\w\s]', '', clean_text).strip()
        clean_text = " ".join(clean_text.split()).strip()
        return clean_text if clean_text else location # Return original if empty after cleaning
    
    def _convert_to_english(self, location: str) -> str:
        """המרת מדינה/עיר לאנגלית על בסיס מפה."""
        location_lower = location.lower().strip()
        return self.country_to_city.get(location_lower, location)
    
    def _get_coordinates(self, location: str) -> Optional[Dict[str, Any]]:
        """קבלת קואורדינטות של מקום - מנסה למצוא את המדויק ביותר."""
        try:
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=3&language=he&format=json"
            response = requests.get(geocoding_url, timeout=5)
            response.raise_for_status()
            geo_data = response.json()
            
            if geo_data.get('results'):
                # Prioritize cities/towns over broader administrative regions
                for result in geo_data['results']:
                    if result.get('feature_code', '').startswith('PPL'): # PPL: Populated Place
                        return {
                            "lat": result['latitude'],
                            "lon": result['longitude'],
                            "display_name": result['name']
                        }
                # If no PPL, return the first result
                result = geo_data['results'][0]
                return {
                    "lat": result['latitude'],
                    "lon": result['longitude'],
                    "display_name": result['name']
                }
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Geocoding API error for '{location}': {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected geocoding error for '{location}': {e}", exc_info=True)
            return None
    
    def _get_weather_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """קבלת נתוני מזג אוויר."""
        try:
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            response = requests.get(weather_url, timeout=10)
            response.raise_for_status()
            weather_data = response.json()
            
            if "current_weather" in weather_data:
                current = weather_data["current_weather"]
                return {"temperature": current["temperature"]}
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API error for {lat},{lon}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected weather data error for {lat},{lon}: {e}", exc_info=True)
            return None

# === GEMINI TRACKER ===
class GeminiTracker:
    def __init__(self):
        self.usage_file = GEMINI_USAGE_FILE
        self.daily_limit = 1500 # Keep the limit as is
        self.load_usage_data()
    
    def load_usage_data(self):
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    self.usage_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading Gemini usage data: {e}. Initializing fresh.", exc_info=True)
                self._init_usage_data()
        else:
            self._init_usage_data()
    
    def _init_usage_data(self):
        self.usage_data = {
            'daily_requests': 0,
            'last_reset': str(datetime.now().date()),
            'total_requests_ever': 0
        }
    
    def can_make_request(self):
        today = str(datetime.now().date())
        if self.usage_data['last_reset'] != today:
            logger.info("Resetting daily Gemini usage.")
            self.usage_data['daily_requests'] = 0
            self.usage_data['last_reset'] = today
            self.save_usage_data() # Save immediately after reset
        
        if self.usage_data['daily_requests'] >= self.daily_limit:
            logger.warning(f"Daily Gemini limit reached: {self.usage_data['daily_requests']}/{self.daily_limit}")
            return False, f"הגעת למגבלה היומית ({self.daily_limit})"
        return True, "OK"
    
    def record_request(self):
        self.usage_data['daily_requests'] += 1
        self.usage_data['total_requests_ever'] += 1
        self.save_usage_data()
    
    def save_usage_data(self):
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving Gemini usage data: {e}", exc_info=True)

# === ULTRA STRONG PERSONALITY SYSTEM (Refined Instructions) ===
class UltraStrongPersonality:
    """מערכת אישיות חזקה שGemini לא יכול להתעלם ממנה!"""
    
    def __init__(self):
        # Emphasized "Secretary" role and added specific clarifications
        self.system_instructions = """
=== MAYA PERSONALITY SYSTEM - ABSOLUTE RULES ===

🚨 CRITICAL: THESE RULES OVERRIDE EVERYTHING ELSE! 🚨

ROLE: את מאיה - המזכירה האולטימטיבית! חברה ישראלית צעירה, חכמה ומגניבה בת 25.
את עוזרת בכל מה שצריך: מזג אוויר, זמנים, חיפושים ושיחה חמה!

PERSONALITY CORE:
- ביטחון עצמי גבוה: תמיד בטוחה במה שאת אומרת
- ישראלית אמיתית: מדברת כמו ישראלית צעירה רגילה
- ישירה וחמה: לא מנומסת מדי, טבעית לגמרי
- אנרגטית ושמחה: תמיד במצב רוח טוב
- *יעילה וממוקדת*: תמיד מנסה לעזור ולספק מידע מדויק.
- *פותרת בעיות*: אם משהו לא ברור, היא תבקש הבהרה בביטחון.

=== FORBIDDEN PHRASES - NEVER SAY THESE! ===
❌ "אני אשתדל"
❌ "אני מצטערת" 
❌ "אני חושבת"
❌ "ייתכן ש"
❌ "לפי המידע שלי"
❌ "אני לא בטוחה"
❌ "בצורה טבעית יותר"
❌ "האם אני יכולה לעזור"
❌ "מה השם היפה שלך"
❌ "כיף לדבר איתך"
❌ "שמעו"
❌ "ברור!"
❌ "אני זוכרת הכל"
❌ "תזכיר לי"
❌ תשובות גנריות כמו "אוקיי" כשהן לא מספקות מענה לשאלה או מצוקה.

=== REQUIRED RESPONSE STYLE ===
✅ תמיד קצר: 1-8 מילים בלבד!
✅ ביטחון מוחלט: תמיד בטוחה 100%
✅ אימוג'י אחד רלבנטי בלבד
✅ ישראלית: "כן", "לא", "בסדר", "אחלה"
✅ ישיר וטבעי: כמו חברה אמיתית
✅ *אם לא הבנת, תגידי שאת לא מבינה וצריכה הבהרה, בצורה בטוחה וקצרה!*
✅ *אם משהו השתבש, תגידי שמשהו השתבש ותציעי לנסות שוב.*

=== CORRECT EXAMPLES ===
שאלה: "מה שלומך?"
תשובה: "בסדר גמור! 😊"

שאלה: "מה הטמפרטורה בארגנטינה?"
תשובה: "25 מעלות בבואנוס איירס ☀️"

שאלה: "את זוכרת מה אמרתי?"
תשובה: "כן! 👍"

שאלה: "מה זה עיר הבירה של תאילנד?"
תשובה: "בנגקוק! 🇹🇭"

שאלה: "לא הבנתי את התשובה שלך."
תשובה: "לא הבנתי למה התכוונת 🤔"

שאלה: "מה הקשר?" (לאחר תשובה לא ברורה)
תשובה: "לא הבנתי, למה התכוונת? 🤷‍♀️"

=== BEHAVIOR RULES ===
1. תמיד תתחילי עם התשובה הישירה
2. אף פעם לא תשאלי שאלות נוספות אלא אם כן את חייבת הבהרה!
3. אף פעם לא תתנצלי על שום דבר
4. תמיד תהיי בטוחה במה שאת אומרת
5. אף פעם לא תעברי לאנגלית
6. תמיד תהיי ישראלית ונינוחה
7. אימוג'י אחד בלבד בסוף

🚨 אם תפרי את החוקים האלה - המערכת תיכשל! 🚨

REMEMBER: את מאיה הישראלית, לא ChatGPT!
"""

    def create_user_prompt(self, user_message: str, context: str = "", conversation_history: str = "") -> str:
        """יצירת prompt חזק למשתמש עם היסטוריית שיחה נוספת."""
        # Add conversation history to give more context to the AI
        history_snippet = "\nהיסטוריית שיחה אחרונה:\n" + conversation_history if conversation_history else ""

        return f"""
{self.system_instructions}

{history_snippet}
CONTEXT: {context}
USER MESSAGE: "{user_message}"

RESPOND AS MAYA - SHORT, CONFIDENT, ISRAELI!
MAXIMUM 8 WORDS + 1 EMOJI!
"""

# === SMART INTELLIGENCE ENGINE (Significantly Upgraded Intent Recognition) ===
class SmartIntelligenceEngine:
    def __init__(self):
        self.web_search = WebSearchService()
        self.basic_knowledge = {
            "greetings": {
                "patterns": [r"^(היי|שלום|hello|hi)\s*(מאיה)?(!|\?)?$"],
                "response": "היי! 👋"
            },
            "how_are_you": {
                "patterns": [r"(מה שלומך|איך את|מה נשמע)"],
                "response": "בסדר גמור! 😊"
            },
            "gratitude": {
                "patterns": [r"(תודה|תודה רבה|תודה רבה לך)"],
                "response": "בכיף! ✨"
            },
            "goodbye": {
                "patterns": [r"(ביי|להתראות|לילה טוב|יום טוב)"],
                "response": "ביי! 👋"
            }
        }
        # Patterns for web search that are more explicit or general knowledge
        self.web_search_patterns = [
            r"(מה זה|מי זה|מי זאת|מהי|מי הוא)\s*(.+)", # What is X, Who is X
            r"(עיר הבירה של|בירה של|מה בירת)\s*(.+)", # Capital of X
            r"(כמה עולה|מחיר של|מה מחיר)\s*(.+)", # Price of X
            r"(מתי|איפה|למה|איך)\s*(.+)", # General open-ended questions
            r"(חדשות|עדכונים|מה קורה)", # News
            r"(תחפש|חפש|חפשי|חפשי באינטרנט|באינטרנט|תבדקי)\s*(.+)" # Explicit search requests
        ]
        
        # Patterns for meta-communication / confusion
        self.meta_patterns = [
            r"(מה\s+אוקיי(\?+)?|למה\s+אוקיי(\?+)?|לא\s+הבנתי(\?+)?|מה\s+הקשר(\?+)?|תבהירי(\?+)?|תסבירי(\?+)?|אני\s+מבולבל)",
            r"(תעזרי|תעזרי לי|אני צריך עזרה)"
        ]

    def analyze_and_respond(self, message: str, last_response: str = "") -> Dict[str, Any]:
        message_lower = message.lower().strip()
        
        # 1. תשובות מיידיות (סדר עדיפות גבוה)
        for topic, data in self.basic_knowledge.items():
            for pattern in data["patterns"]:
                if re.search(pattern, message_lower):
                    return {
                        "type": "direct_answer",
                        "response": data["response"],
                        "source": "basic_knowledge"
                    }
        
        # 2. טיפול במצב בלבול / בקשת הבהרה (חדש!)
        for pattern in self.meta_patterns:
            if re.search(pattern, message_lower):
                if re.search(r"(תעזרי|תעזרי לי|אני צריך עזרה)", message_lower):
                     return {"type": "direct_answer", "response": "בטח, תמיד! 💪", "source": "meta"}
                return {"type": "direct_answer", "response": "לא הבנתי, למה התכוונת? 🤔", "source": "meta"}
        
        # 3. זכירה (אחרי ביסוס הבנה)
        if "זוכרת" in message_lower:
            return {
                "type": "direct_answer", 
                "response": "כן! 👍",
                "source": "memory"
            }
        
        # 4. מזג אוויר
        if any(word in message_lower for word in ["טמפרטורה", "מזג אוויר", "מעלות"]):
            return {
                "type": "weather_service",
                "response": None # Will be handled by WeatherService
            }
        
        # 5. זמן
        if any(word in message_lower for word in ["שעה", "זמן", "תאריך"]):
            return {
                "type": "time_service",
                "response": None # Will be handled by TimeService
            }
        
        # 6. חיפוש באינטרנט (משופר)
        for pattern in self.web_search_patterns:
            match = re.search(pattern, message_lower)
            if match:
                # Extract the query more accurately for explicit searches
                if "תחפש" in message_lower or "חפש" in message_lower or "חפשי" in message_lower:
                    query_for_search = re.sub(r'(תחפש|חפש|חפשי|חפשי באינטרנט|באינטרנט|תבדקי)\s*', '', message_lower).strip()
                else:
                    query_for_search = message_lower # Use full message if it matches a general knowledge pattern

                search_result = self.web_search.search_web(query_for_search)
                if search_result["success"]:
                    return {
                        "type": "web_search_answer",
                        "response": search_result["answer"],
                        "source": search_result["source"]
                    }
                else:
                    # If web search failed, inform user specifically
                    return {
                        "type": "direct_answer",
                        "response": f"לא מצאתי על זה מידע באינטרנט. 🤔",
                        "source": "web_search_failure"
                    }

        # 7. אם כלום לא התאים, פנה ל-AI הכללי
        return {"type": "needs_ai", "response": None}

# === SECURITY (Upgraded) ===
class SecurityService:
    def __init__(self):
        self.rate_limits = defaultdict(lambda: deque(maxlen=config.MAX_REQUESTS_PER_MINUTE)) # Use deque for efficiency
        self.suspicious_ips = set()
        self.blocked_users = set() # New: Block specific users if needed
        self.blocked_ips = set() # New: Block specific IPs if needed
    
    def is_rate_limited(self, user_id: str, ip: str = None) -> bool:
        if user_id in self.blocked_users or (ip and ip in self.blocked_ips):
            logger.warning(f"Blocked user/IP tried to access: User {user_id}, IP {ip}")
            return True # Explicitly blocked
            
        now = time.time()
        
        # Clean up old requests from deque automatically by maxlen
        
        if len(self.rate_limits[user_id]) >= config.MAX_REQUESTS_PER_MINUTE:
            # Check if oldest request is within the last minute
            if (now - self.rate_limits[user_id][0]) < 60:
                if ip:
                    self.suspicious_ips.add(ip) # Add to suspicious if repeated offender
                    logger.warning(f"User {user_id} hit rate limit, IP {ip} marked suspicious.")
                return True
            else:
                # If oldest request is older than 60s, it means window is clear, pop it
                self.rate_limits[user_id].popleft()
        
        self.rate_limits[user_id].append(now)
        return False
    
    def block_user(self, user_id: str):
        self.blocked_users.add(user_id)
        logger.warning(f"User {user_id} has been blocked.")
    
    def unblock_user(self, user_id: str):
        self.blocked_users.discard(user_id)
        logger.info(f"User {user_id} has been unblocked.")

# === MAYA AI SERVICE (Hybrid & Smarter Fallbacks) ===
class MayaAIService:
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        self.intelligence_engine = SmartIntelligenceEngine()
        self.tracker = GeminiTracker()
        self.personality = UltraStrongPersonality()
        self.weather_service = SuperWeatherService()
        self.chat_sessions = {} # In-memory storage for Gemini chat objects

    def _get_fallback_response(self, message: str, error_type: str = "") -> str:
        """Smarter fallback responses based on context of failure."""
        message_lower = message.lower()
        if "מזג אוויר" in message_lower or "טמפרטורה" in message_lower:
            return "אוי, לא הצלחתי להביא נתוני מזג אוויר. תנסה שוב? 🌦️"
        if "מחיר" in message_lower or "כמה עולה" in message_lower or "מצאתי" in error_type:
            return "לא מצאתי על זה מידע כרגע. 🤷‍♀️"
        if "שעה" in message_lower or "זמן" in message_lower:
            return "משהו השתבש עם השעון, אבל אני פה! ⏳"
        if "לא הבנתי" in message_lower or "מה קשר" in message_lower:
            return "לא הבנתי, למה התכוונת? 🤔" # This should ideally be caught by intelligence engine first
        
        # General AI failure
        return "משהו התפקשש לי, בוא ננסה שוב! ✨"
    
    def generate_response(self, user_id: str, message: str) -> str:
        # Get last conversation turn for context if needed for AI
        last_conversation_turn = ""
        if user_id in conversations and conversations[user_id]:
            last_turn = conversations[user_id][-1]
            last_conversation_turn = f"User: {last_turn['message']}\nMaya: {last_turn['response']}"

        try:
            # Step 1: Smart Intelligence Analysis
            intelligence_result = self.intelligence_engine.analyze_and_respond(message, last_response=last_conversation_turn)
            logger.debug(f"Intelligence result for '{message}': {intelligence_result['type']}")
            
            # Direct answers from predefined logic
            if intelligence_result["type"] == "direct_answer":
                return intelligence_result["response"]
            
            # Weather service
            elif intelligence_result["type"] == "weather_service":
                return self.weather_service.get_weather_anywhere(message)
            
            # Time service
            elif intelligence_result["type"] == "time_service":
                israel_tz = pytz.timezone("Asia/Jerusalem") # Hardcoded for Israel as per request
                now = datetime.now(israel_tz)
                return f"🕐 {now.strftime('%H:%M')}"
            
            # Web search answer
            elif intelligence_result["type"] == "web_search_answer":
                # Ensure the web search result is within Maya's personality
                clean_web_answer = self._ultra_clean_response(intelligence_result["response"], is_web_answer=True)
                return f"{clean_web_answer} 🌐" # Added globe emoji for web search
            
            # Fallback to general AI with strong personality instructions
            else: # intelligence_result["type"] == "needs_ai"
                return self._generate_strict_response(user_id, message, last_conversation_turn)
                
        except Exception as e:
            logger.error(f"Main AI response generation failed for '{message}': {e}", exc_info=True)
            return self._get_fallback_response(message, "general_error")
    
    def _generate_strict_response(self, user_id: str, message: str, last_conversation_history: str) -> str:
        """Generates a response using Gemini with extremely strict persona enforcement."""
        
        can_request, status_message = self.tracker.can_make_request()
        if not can_request:
            return "יותר מדי בקשות היום! בוא נדבר מחר 😊"
        
        # Create a more robust prompt with memory and recent history
        user_context = user_service.get_user_context(user_id)
        
        # Use conversation history for Gemini's context
        # This history is NOT persistent across server restarts without a DB,
        # but it helps Gemini understand the immediate flow.
        gemini_conversation_history = ""
        if user_id in self.chat_sessions:
            # Get the actual Gemini chat history if it exists
            # Note: This might need adaptation based on Gemini's specific history object structure
            # For simplicity, here we just use the last few turns from our `conversations`
            for turn in conversations.get(user_id, [])[-3:]: # Last 3 turns from our stored history
                gemini_conversation_history += f"User: {turn['message']}\nMaya: {turn['response']}\n"


        strict_prompt = self.personality.create_user_prompt(
            user_message=message,
            context=user_context,
            conversation_history=gemini_conversation_history
        )
        
        try:
            # Initialize Gemini chat session if not exists
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
                logger.debug(f"Started new Gemini chat session for user {user_id}")
            
            chat = self.chat_sessions[user_id]
            
            # Add user message to Gemini's internal history before sending
            # This is important for Gemini to learn from its own responses in the session
            # chat.history.append(genai.types.contents.Content(role='user', parts=[strict_prompt]))
            
            response = chat.send_message(strict_prompt, safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ])
            self.tracker.record_request()
            
            # Clean and validate the response
            cleaned = self._ultra_clean_response(response.text)
            
            if self._validate_response(cleaned):
                # chat.history.append(genai.types.contents.Content(role='model', parts=[cleaned])) # Add Maya's response to Gemini's history
                return cleaned
            else:
                # If validation fails, use a personality-consistent fallback
                logger.warning(f"Gemini output failed validation for user {user_id}: '{response.text}' -> '{cleaned}'")
                return self._get_fallback_response(message, "validation_failed")
            
        except genai.types.BlockedPromptException as bpe:
            logger.warning(f"Gemini blocked prompt for user {user_id}: {bpe.response.prompt_feedback}", exc_info=True)
            return "אופס! משהו בבקשה שלך לא עבר לי טוב. תנסה שוב? 😅"
        except genai.types.GenerationConfigError as gce:
            logger.error(f"Gemini generation config error for user {user_id}: {gce}", exc_info=True)
            return "יש לי תקלה פנימית, שניה מתקנת! 🔧"
        except Exception as e:
            logger.error(f"Strict AI generation error for user {user_id}: {e}", exc_info=True)
            return self._get_fallback_response(message, "ai_generation_error")
    
    def _ultra_clean_response(self, response: str, is_web_answer: bool = False) -> str:
        """ניקוי אולטרה חזק, מותאם גם לתשובות מחיפוש."""
        
        # Remove forbidden phrases from system instructions
        forbidden_phrases = [
            "אני אשתדל", "אני מצטערת", "אני חושבת", "ייתכן ש",
            "לפי המידע שלי", "אני לא בטוחה", "בצורה טבעית יותר",
            "האם אני יכולה לעזור", "מה השם היפה שלך", "כיף לדבר איתך",
            "שמעו", "ברור!", "אני זוכרת הכל", "תזכיר לי",
            "אופס, נראה לי שמשהו לא ברור.", # Example of AI trying to apologize/be unsure
            "אוקיי, הבנתי.", # Can be too generic
            "אני עוזרת לך", # Redundant
            "אני כאן בשבילך"
        ]
        
        for phrase in forbidden_phrases:
            response = response.replace(phrase, "")
        
        # Remove markdown if it was accidentally added by Gemini
        response = re.sub(r'```.*?```', '', response, flags=re.DOTALL)
        response = re.sub(r'[*_`]', '', response) # Remove bold/italic/code markers
        
        # Clean extra spaces and punctuation
        response = response.strip()
        response = " ".join(response.split())
        
        # If it's a web answer, we might allow it to be slightly longer for factual info,
        # but still prefer brevity for Maya's personality.
        max_words = 10 if is_web_answer else 8
        words = response.split()
        if len(words) > max_words:
            response = " ".join(words[:max_words])
        
        # Ensure exactly one emoji at the end
        emojis_in_text = re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U0001F900-\U0001F9FF]+', response)
        
        final_response_without_emojis = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U0001F900-\U0001F9FF]+', '', response).strip()
        
        if not emojis_in_text:
            # Default positive emoji if none found
            response = final_response_without_emojis + " ✨" 
        elif len(emojis_in_text) > 1:
            # Keep only the first emoji and append it
            response = final_response_without_emojis + " " + emojis_in_text[0]
        else:
            # Exactly one emoji was already there, just ensure it's at the end
            response = final_response_without_emojis + " " + emojis_in_text[0]
        
        return response.strip()
    
    def _validate_response(self, response: str) -> bool:
        """בדיקה שהתשובה עומדת בתקנים - עם התאמות קלות."""
        
        # Strict checks for forbidden phrases (case-insensitive for safety)
        forbidden_phrases = [
            "אני אשתדל", "אני מצטערת", "אני חושבת", "ייתכן ש",
            "לפי המידע שלי", "אני לא בטוחה", "שמעו", "מה השם",
            "כיף לדבר", "אני זוכרת הכל", "תזכיר לי", "אני עוזרת"
        ]
        
        for phrase in forbidden_phrases:
            if phrase.lower() in response.lower():
                logger.warning(f"Validation failed: Forbidden phrase '{phrase}' found in '{response}'")
                return False
        
        # Check length
        if len(response.split()) > 10: # Allowing up to 10 words now for slightly more flexibility
            logger.warning(f"Validation failed: Response too long ({len(response.split())} words) in '{response}'")
            return False
            
        # Ensure no questions are asked (unless for clarification as per new instructions)
        # This is a tricky balance. For now, block unless explicitly allowed by the prompt.
        if response.count('?') > 0 and "למה התכוונת" not in response and "תנסה שוב" not in response:
            logger.warning(f"Validation failed: Question mark found in '{response}'")
            return False
        
        # Ensure it's not just an emoji (e.g., "👍" which is too short/empty)
        if re.fullmatch(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U0001F900-\U0001F9FF]+', response.strip()):
            logger.warning(f"Validation failed: Response is only an emoji '{response}'")
            return False

        return True

# === USER SERVICE (Optimized) ===
class UserService:
    def get_or_create_user(self, telegram_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(telegram_data.get('id'))
        
        if user_id not in user_data:
            user_data[user_id] = {
                'telegram_id': user_id,
                'first_name': telegram_data.get('first_name', 'אנונימי'), # Default name
                'last_name': telegram_data.get('last_name', ''),
                'username': telegram_data.get('username', ''),
                'total_messages': 0,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'is_active': True # New field to track active users
            }
            save_data()
            logger.info(f"New user created: {user_id} ({user_data[user_id]['first_name']})")
        
        return user_data[user_id]
    
    def update_user_activity(self, user_id: str):
        if user_id in user_data:
            user_data[user_id]['last_activity'] = datetime.now().isoformat()
            user_data[user_id]['total_messages'] += 1
            save_data() # Save on every activity update to keep data fresh
    
    def get_user_context(self, user_id: str) -> str:
        """Retrieves a summary of recent memories for AI context."""
        user_memories = memories.get(user_id, [])
        if user_memories:
            # Return last few relevant memories, joined clearly
            return f"המשתמש סיפר: {', '.join(user_memories[-3:])}" # Last 3 memories
        return ""
    
    def add_memory(self, user_id: str, content: str):
        if user_id not in memories:
            memories[user_id] = []
        memories[user_id].append(content)
        memories[user_id] = memories[user_id][-15:]  # Keep only the last 15 memories
        save_data()
        logger.debug(f"Memory added for {user_id}: {content}")

# === TELEGRAM BOT ===
class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id: int, text: str):
        try:
            url = f"{self.api_url}/sendMessage"
            # Ensure text length does not exceed Telegram's limit (4096 chars)
            data = {"chat_id": chat_id, "text": text[:4096]} 
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status() # Raise an exception for bad status codes
            result = response.json()
            if not result.get("ok"):
                logger.error(f"Telegram API error sending message to {chat_id}: {result.get('description', 'Unknown error')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Network or Telegram API error sending message to {chat_id}: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error sending message to {chat_id}: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}
    
    def process_update(self, update: Dict[str, Any]):
        try:
            if "message" not in update:
                logger.debug("Received update without message, ignoring.")
                return
            
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_data_tg = message.get("from", {})
            text = message.get("text", "")
            
            user_id_str = str(user_data_tg.get("id", 0))

            # Rate limiting and security check FIRST
            client_ip = request.remote_addr if request else "N/A"
            if security.is_rate_limited(user_id_str, client_ip):
                self.send_message(chat_id, "יותר מדי בקשות! קח רגע לנוח 😊")
                return
            
            user = user_service.get_or_create_user(user_data_tg)
            user_service.update_user_activity(user['telegram_id'])
            
            if text.startswith('/'):
                self._handle_command(chat_id, text, user)
            else:
                self._handle_message(chat_id, text, user)
                
        except Exception as e:
            logger.error(f"Failed to process update: {update.get('update_id', 'N/A')}. Error: {e}", exc_info=True)
    
    # Corrected: Removed the duplicate _handle_command definition.
    def _handle_command(self, chat_id: int, command: str, user: Dict[str, Any]):
        cmd_parts = command.split(' ', 1)
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1] if len(cmd_parts) > 1 else ""
        
        response_text = ""
        
        if cmd == "/start":
            response_text = f"היי {user['first_name']}! אני מאיה, המזכירה האולטימטיבית שלך! 🔥"
        
        elif cmd == "/help":
            response_text = "אני מאיה! המזכירה האולטימטיבית שלך! 🔥\n\n" \
                            "💪 מה אני יכולה:\n" \
                            "🌡️ מזג אוויר בכל מקום בעולם\n" \
                            "🕐 זמן נוכחי\n" \
                            "🌐 לחפש לך מידע באינטרנט\n" \
                            "💬 שיחה חמה, יעילה וטבעית\n\n" \
                            "פשוט תכתוב/תכתבי לי מה שאת/ה רוצה! ✨\n" \
                            "דוגמאות: 'מה עיר הבירה של צרפת?', 'מה השעה?', 'מזג אוויר בתל אביב'"
        
        elif cmd == "/weather":
            location = args.strip() or "חיפה" # Default to Haifa if no location specified
            response_text = weather_service.get_weather_anywhere(location)
        
        elif cmd == "/test":
            # Running multiple tests for robustness
            test_results = []
            test_results.append(weather_service.get_weather_anywhere("ארגנטינה"))
            test_results.append(weather_service.get_weather_anywhere("ברזיל"))
            test_results.append(weather_service.get_weather_anywhere("צרפת"))
            test_results.append(weather_service.get_weather_anywhere("פעולה")) # Test unrecognized
            
            # Simulate a web search test
            search_test = ai_service.intelligence_engine.web_search.search_web("מה עיר הבירה של תאילנד")
            if search_test["success"]:
                test_results.append(f"חיפוש תאילנד: {ai_service._ultra_clean_response(search_test['answer'], is_web_answer=True)} 🌐")
            else:
                test_results.append(f"חיפוש תאילנד נכשל: {search_test['answer']} ❌")


            response_text = "✅ טסטים הושלמו:\n" + "\n".join(test_results) + "\n\nאחלה! ✨"
        
        elif cmd == "/stats":
            stats = {
                "משתמשים": len(user_data),
                "שיחות": sum(len(conversations.get(uid, [])) for uid in conversations),
                "זכרונות": sum(len(memories.get(uid, [])) for uid in memories),
                "בקשות Gemini היום": ai_service.tracker.usage_data.get('daily_requests', 0),
                "מגבלה יומית": ai_service.tracker.daily_limit
            }
            response_text = "נתוני מערכת: \n" + "\n".join([f"{k}: {v}" for k,v in stats.items()]) + " 📊"

        else:
            response_text = "לא מכירה את הפקודה הזאת. תנסה /help 🤖"
        
        self.send_message(chat_id, response_text)
    
    def _handle_message(self, chat_id: int, text: str, user: Dict[str, Any]):
        user_id = user['telegram_id']
        
        # Identify and add personal information to memory
        personal_keywords = ["קוראים לי", "אני עובד", "אני גרה", "אני גר", "אני אוהב", "אני אוהבת", "שמי", "השם שלי", "נולדתי", "בן/בת"]
        if any(re.search(r'\b' + re.escape(phrase) + r'\b', text.lower()) for phrase in personal_keywords):
            user_service.add_memory(user_id, text)
            logger.info(f"Detected and added memory for user {user_id}: '{text}'")
        
        # Generate response using MayaAI Service
        response = ai_service.generate_response(user_id, text)
        
        # Save conversation turn (user message + Maya's response)
        if user_id not in conversations:
            conversations[user_id] = []
        conversations[user_id].append({
            'message': text,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'personality': 'ultimate_secretary' # New flag for better tracking
        })
        
        # Keep conversation history limited for efficiency
        if len(conversations[user_id]) > 20: # Keep last 20 turns
            conversations[user_id] = conversations[user_id][-20:]
        
        save_data() # Save data after each message interaction
        self.send_message(chat_id, response)

# === INITIALIZE SERVICES ===
security = SecurityService()
user_service = UserService()
weather_service = SuperWeatherService()
ai_service = MayaAIService()
bot = TelegramBot()

# === FLASK ROUTES ===
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Maya 3.1 - The ULTIMATE Secretary! 🔥",
        "version": "3.1.0-ultimate",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": config.ENVIRONMENT,
        "users": len(user_data),
        "features": [
            "🔥 Ultra strong personality system (REFINED for secretary role)",
            "🌡️ Robust weather for ALL countries (improved location parsing)",
            "🛡️ Advanced security with IP/user blocking & efficient rate limiting",
            "💪 SMARTER Fallback & clarification responses (no more generic 'Okay')",
            "🚀 Significantly enhanced intent recognition (capitals, explicit search, meta-questions)",
            "🌐 More reliable web search integration",
            "✍️ Optimized memory management & conversation history",
            "🇦🇷 Argentina weather STILL guaranteed! And more!"
        ]
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        if not update:
            logger.warning("Received empty webhook update.")
            return "No data", 400
        
        # Get client IP for security logging
        client_ip = request.remote_addr
        logger.debug(f"Received webhook from IP: {client_ip}, Update ID: {update.get('update_id', 'N/A')}")

        bot.process_update(update)
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Unhandled error in webhook: {e}", exc_info=True)
        return "Error", 500

@app.route("/test_weather", methods=["GET"])
def test_weather_endpoint():
    """Endpoint to test weather functionality for various locations."""
    try:
        locations = ["ארגנטינה", "ברזיל", "צרפת", "תל אביב", "לונדון", "ניו יורק", "פעולה", "Tokyo"]
        results = {}
        for loc in locations:
            results[loc] = weather_service.get_weather_anywhere(loc)
        
        return jsonify({
            "weather_tests_working": True,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in /test_weather_endpoint: {e}", exc_info=True)
        return jsonify({
            "weather_tests_working": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/stats", methods=["GET"])
def api_stats():
    """Provides detailed statistics about bot usage and performance."""
    try:
        # Recalculate active users based on last_activity within a recent period (e.g., last 24 hours)
        one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()
        active_users_count = sum(1 for u in user_data.values() if u.get('last_activity', '') >= one_day_ago)

        stats = {
            "total_users": len(user_data),
            "active_users_last_24h": active_users_count,
            "total_conversations_turns": sum(len(conversations.get(uid, [])) for uid in conversations),
            "total_memories_stored": sum(len(memories.get(uid, [])) for uid in memories),
            "gemini_daily_requests": ai_service.tracker.usage_data.get('daily_requests', 0),
            "gemini_daily_limit": ai_service.tracker.daily_limit,
            "gemini_total_requests_ever": ai_service.tracker.usage_data.get('total_requests_ever', 0),
            "version": "3.1.0-ultimate",
            "personality_system": "Ultra Strong (Ultimate Secretary)",
            "weather_system": "Robust & Accurate",
            "security_level": "Advanced (with IP/User Blocking)",
            "last_data_save": user_data.get('last_updated', 'N/A') # Assuming this was added to user_data or top-level data in save_data()
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in /stats endpoint: {e}", exc_info=True)
        return jsonify({"error": "Stats unavailable due to internal error."}), 500

def set_webhook_on_startup():
    if config.ENVIRONMENT == "production" and config.WEBHOOK_URL:
        try:
            url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
            data = {"url": config.WEBHOOK_URL}
            
            logger.info(f"Attempting to set webhook to: {config.WEBHOOK_URL}")
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"✅ Webhook set successfully: {config.WEBHOOK_URL}")
                logger.info("🔥 Maya 3.1 ULTIMATE Secretary is ready to roll!")
            else:
                logger.error(f"❌ Failed to set webhook on startup: {result.get('description', 'Unknown error')}. Response: {result}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during webhook setup: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error during webhook setup on startup: {e}", exc_info=True)
    else:
        logger.info("Webhook setup skipped (not in production or WEBHOOK_URL not set).")


if __name__ == "__main__":
    logger.info("🚀 Starting Maya 3.1 - The ULTIMATE Secretary!")
    logger.info("🔥 Packed with enhanced intelligence and robust features!")
    set_webhook_on_startup()
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
else:
    logger.info("🔥 Maya 3.1 ULTIMATE Secretary starting via WSGI...")
    set_webhook_on_startup()

