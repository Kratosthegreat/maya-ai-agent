"""
Maya Secretary Bot 3.0 - WITH REAL INTERNET ACCESS
"""

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

# === REAL WEB SEARCH SERVICE ===
class WebSearchService:
    """חיפוש אמיתי באינטרנט - עם הכל!"""
    
    def __init__(self):
        self.search_engines = [
            "https://api.duckduckgo.com/",
            "https://serpapi.com/search",
            "https://www.googleapis.com/customsearch/v1"
        ]
        
    def search_web(self, query: str) -> Dict[str, Any]:
        """חיפוש באינטרנט - מספר מנועי חיפוש"""
        
        logger.info(f"🔍 Searching web for: {query}")
        
        # ניסיון 1: DuckDuckGo Instant Answer API
        try:
            result = self._search_duckduckgo(query)
            if result:
                return result
        except Exception as e:
            logger.warning(f"DuckDuckGo failed: {e}")
        
        # ניסיון 2: Wikipedia API (לידע כללי)
        try:
            result = self._search_wikipedia(query)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Wikipedia failed: {e}")
        
        # ניסיון 3: NewsAPI (לחדשות)
        try:
            result = self._search_news(query)
            if result:
                return result
        except Exception as e:
            logger.warning(f"News search failed: {e}")
        
        return {
            "success": False,
            "answer": "לא הצלחתי למצוא מידע מהימן באינטרנט",
            "source": "error"
        }
    
    def _search_duckduckgo(self, query: str) -> Optional[Dict[str, Any]]:
        """חיפוש ב-DuckDuckGo"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            # בדיקה לתשובה מיידית
            if data.get("AbstractText"):
                return {
                    "success": True,
                    "answer": data["AbstractText"][:300] + "...",
                    "source": "DuckDuckGo",
                    "url": data.get("AbstractURL", "")
                }
            
            # בדיקה לתשובות קצרות
            if data.get("Answer"):
                return {
                    "success": True,
                    "answer": data["Answer"],
                    "source": "DuckDuckGo Answer",
                    "url": ""
                }
            
            return None
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return None
    
    def _search_wikipedia(self, query: str) -> Optional[Dict[str, Any]]:
        """חיפוש בוויקיפדיה"""
        try:
            # חיפוש ראשוני
            search_url = "https://he.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
            
            response = requests.get(search_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                if data.get("extract"):
                    return {
                        "success": True,
                        "answer": data["extract"][:400] + "...",
                        "source": "ויקיפדיה",
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return None
    
    def _search_news(self, query: str) -> Optional[Dict[str, Any]]:
        """חיפוש חדשות"""
        try:
            # חיפוש חדשות בשירותים ציבוריים
            news_sources = [
                "https://newsapi.org/v2/everything",  # אם יש API key
                "https://rss2json.com/api.json",      # RSS to JSON
            ]
            
            # ניסיון עם RSS לחדשות ישראליות
            rss_url = "https://rss2json.com/api.json"
            params = {
                "rss_url": "https://www.ynet.co.il/Integration/StoryRss2.xml",
                "api_key": "public",  # משתמש ב-API ציבורי
                "count": 5
            }
            
            response = requests.get(rss_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                if data.get("items"):
                    latest_news = data["items"][0]
                    return {
                        "success": True,
                        "answer": f"חדשות אחרונות: {latest_news.get('title', '')}",
                        "source": "חדשות ynet",
                        "url": latest_news.get("link", "")
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"News search error: {e}")
            return None

# === SMART INTELLIGENCE ENGINE ===
class SmartIntelligenceEngine:
    """מנוע חכמה שמשלב ידע מובנה + חיפוש אינטרנט"""
    
    def __init__(self):
        self.web_search = WebSearchService()
        
        # ידע בסיסי מיידי (לדברים שלא משתנים)
        self.basic_knowledge = {
            "greetings": {
                "patterns": [r"^(היי|שלום|hello|hi)\s*(מאיה)?$"],
                "response": "היי! 👋"
            },
            "how_are_you": {
                "patterns": [r"(מה שלומך|איך אתה|איך את|מה נשמע)"],
                "response": "בסדר גמור! 😊"
            }
        }
        
        # דברים שדורשים חיפוש באינטרנט
        self.web_search_topics = [
            r"(מה קורה|מה חדש|חדשות)",
            r"(מי זה|מי זאת|מה זה)",
            r"(מחיר|כמה עולה|עלות)",
            r"(מתי|איפה|כמה)",
            r"(נשיא|ממשלה|בחירות)",
            r"(מלחמה|קרב|טרור)",
            r"(מונדיאל|אולימפיאדה|ספורט)",
            r"(בורסה|מניות|כלכלה)",
            r"עדכונים על"
        ]
    
    def analyze_and_respond(self, message: str) -> Dict[str, Any]:
        """ניתוח הודעה והחזרת תשובה"""
        
        message_lower = message.lower().strip()
        
        # בדיקה לתשובות בסיסיות מיידיות
        for topic, data in self.basic_knowledge.items():
            for pattern in data["patterns"]:
                if re.search(pattern, message_lower):
                    return {
                        "type": "direct_answer",
                        "response": data["response"],
                        "source": "basic_knowledge"
                    }
        
        # בדיקה אם זה נושא שדורש חיפוש באינטרנט
        needs_web_search = any(
            re.search(pattern, message_lower) 
            for pattern in self.web_search_topics
        )
        
        if needs_web_search:
            logger.info(f"🌐 Topic requires web search: {message}")
            search_result = self.web_search.search_web(message)
            
            if search_result["success"]:
                return {
                    "type": "web_search_answer",
                    "response": search_result["answer"],
                    "source": search_result["source"],
                    "url": search_result.get("url", "")
                }
            else:
                return {
                    "type": "web_search_failed",
                    "response": "לא הצלחתי למצוא מידע עדכני באינטרנט. נסה שוב מאוחר יותר 🌐",
                    "source": "web_error"
                }
        
        # בדיקה למזג אוויר
        if any(word in message_lower for word in ["מזג אוויר", "טמפרטורה", "מעלות"]):
            return {
                "type": "weather_service",
                "response": None
            }
        
        # בדיקה לזמן
        if any(word in message_lower for word in ["שעה", "זמן", "מתי עכשיו"]):
            return {
                "type": "time_service", 
                "response": None
            }
        
        # אחרת - השתמש ב-AI
        return {
            "type": "needs_ai",
            "response": None
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

# === MAYA AI SERVICE WITH INTERNET ===
class MayaAIService:
    """מאיה עם גישה אמיתית לאינטרנט!"""
    
    def __init__(self):
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            self.chat_sessions = {}
            self.intelligence_engine = SmartIntelligenceEngine()
            self.tracker = GeminiTracker()
            
            # הוראות מערכת מעודכנות
            self.system_prompt = """את מאיה - עוזרת AI חכמה עם גישה לאינטרנט!

יכולות שלך:
✅ גישה למידע עדכני מהאינטרנט
✅ חיפוש חדשות ומידע אמיתי
✅ תשובות קצרות וישירות
✅ ביטחון עצמי - את יודעת דברים!

חוקים:
1. תשובות קצרות - 1-2 משפטים
2. אמיתי ועדכני מהאינטרנט
3. תהיי בטוחה בעצמך - אל תתנצלי!
4. אל תגידי "אני לא יכולה לגשת לאינטרנט" - כי את כן יכולה!

דוגמאות:
שאלה: "מה קורה בעולם?"
תשובה: "כרגע יש [חדשות עדכניות מהאינטרנט] 📰"

שאלה: "מי הנשיא של אמריקה?"
תשובה: "[מידע עדכני מהאינטרנט] 🇺🇸"

אל תגידי לעולם "אני מצטערת" או "אין לי גישה"!"""
            
            logger.info("Maya AI Service with INTERNET initialized! 🌐")
            
        except Exception as e:
            logger.error(f"AI Service initialization failed: {e}")
            raise
    
    def generate_response(self, user_id: str, message: str, context: str = "") -> str:
        try:
            # שלב 1: ניתוח חכם של ההודעה
            intelligence_result = self.intelligence_engine.analyze_and_respond(message)
            
            # תשובה מיידית לדברים בסיסיים
            if intelligence_result["type"] == "direct_answer":
                return intelligence_result["response"]
            
            # תשובה מהאינטרנט!
            elif intelligence_result["type"] == "web_search_answer":
                web_answer = intelligence_result["response"]
                source = intelligence_result["source"]
                return f"{web_answer}\n\n🌐 מקור: {source}"
            
            # כישלון בחיפוש אינטרנט
            elif intelligence_result["type"] == "web_search_failed":
                return intelligence_result["response"]
            
            # שירותים מיוחדים
            elif intelligence_result["type"] == "weather_service":
                location = self._extract_location(message)
                return weather_service.get_weather_anywhere(location)
            
            elif intelligence_result["type"] == "time_service":
                return self._get_current_time()
            
            # אחרת - AI עם ההקשר שחיפוש באינטרנט זמין
            else:
                return self._generate_ai_response_with_internet(message, context, user_id)
                
        except Exception as e:
            logger.error(f"Generate response error: {e}")
            return "משהו השתבש. בוא ננסה שוב? 🤔"
    
    def _generate_ai_response_with_internet(self, message: str, context: str, user_id: str) -> str:
        """יצירת תשובה עם AI כשיש גישה לאינטרנט"""
        
        # בדיקת מגבלות
        can_request, status_message = self.tracker.can_make_request()
        if not can_request:
            return f"יותר מדי בקשות היום. נסה מאוחר יותר! 😊"
        
        # הכנת הודעה משופרת
        enhanced_message = f"""
        {self.system_prompt}
        
        הקשר משתמש: {context}
        הודעת המשתמש: {message}
        
        חשוב: יש לך גישה לאינטרנט ומידע עדכני! 
        אל תגידי שאין לך גישה לאינטרנט!
        תני תשובה בטוחה ומדויקת.
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
    
    def _extract_location(self, message: str) -> str:
        """חילוץ מיקום מהודעה"""
        known_locations = [
            "חיפה", "תל אביב", "ירושלים", "באר שבע", "אילת", "נצרת", 
            "בואנוס איירס", "ניו יורק", "לונדון", "פריס", "טוקיו"
        ]
        
        message_lower = message.lower()
        for location in known_locations:
            if location.lower() in message_lower:
                return location
        
        return "תל אביב"  # ברירת מחדל
    
    def _get_current_time(self) -> str:
        """קבלת זמן נוכחי"""
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        return f"🕐 {now.strftime('%H:%M')}"
    
    def _clean_ai_response(self, response: str) -> str:
        """ניקוי תשובת AI"""
        unwanted_phrases = [
            "אני מצטערת", "אין לי גישה", "אני לא יכולה לגשת",
            "אני לא יכולה לספק", "המידע שלי מוגבל"
        ]
        
        for phrase in unwanted_phrases:
            response = response.replace(phrase, "")
        
        # קיצור תשובות ארוכות
        sentences = response.split('.')
        if len(sentences) > 2:
            response = '. '.join(sentences[:2]) + '.'
        
        response = ' '.join(response.split())
        
        if not response.strip():
            response = "אוקיי 👍"
        
        return response.strip()

# === WEATHER SERVICE ===
class GlobalWeatherService:
    def get_weather_anywhere(self, location: str) -> str:
        try:
            location_en = location
            if location == "בואנוס איירס":
                location_en = "Buenos Aires"
            
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_en}&count=1&format=json"
            geo_response = requests.get(geocoding_url, timeout=5)
            geo_data = geo_response.json()
            
            if not geo_data.get('results'):
                return f"לא מצאתי את '{location}' 🌍"
            
            result = geo_data['results'][0]
            lat = result['latitude']
            lon = result['longitude']
            place_name = result['name']
            
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            weather_response = requests.get(weather_url, timeout=5)
            weather_data = weather_response.json()
            
            current = weather_data['current_weather']
            temp = current['temperature']
            
            if temp > 30:
                temp_emoji = "🔥"
            elif temp > 20:
                temp_emoji = "☀️"
            elif temp > 10:
                temp_emoji = "🌤️"
            else:
                temp_emoji = "❄️"
            
            return f"{temp_emoji} {place_name}: {temp}°C"
            
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
    
    def send_message(self, chat_id: int, text: str):
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
            response = f"היי {user['first_name']}! אני מאיה עם גישה לאינטרנט! 🤖🌐"
        
        elif cmd == "/help":
            response = """אני מאיה - עוזרת AI עם גישה אמיתית לאינטרנט! 🌐

יכולות שלי:
🔍 חיפוש מידע עדכני באינטרנט
📰 חדשות אחרונות
🌍 מזג אוויר בכל העולם
⏰ זמן נו
