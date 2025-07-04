import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests
import pytz
from typing import Dict, Any, Optional
import time

# Third-party imports
import google.generativeai as genai
from config import config

# === ENHANCED LOGGING SETUP ===
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        
        remaining = self.daily_limit - self.usage_data['daily_requests']
        return True, f"OK (נותרו: {remaining})"
    
    def record_request(self, tokens_used=0):
        now = datetime.now()
        self.usage_data['daily_requests'] += 1
        self.usage_data['total_requests_ever'] += 1
        self.usage_data['minute_requests'].append(now.isoformat())
        self.usage_data['total_tokens'] += tokens_used
        self.save_usage_data()
        logger.info(f"Recorded: {self.usage_data['daily_requests']}/{self.daily_limit}, Tokens: {tokens_used}")
    
    def get_usage_stats(self):
        return {
            'daily_requests': self.usage_data['daily_requests'],
            'daily_limit': self.daily_limit,
            'daily_remaining': self.daily_limit - self.usage_data['daily_requests'],
            'total_tokens': self.usage_data['total_tokens'],
            'total_requests_ever': self.usage_data['total_requests_ever'],
            'percentage_used_today': round((self.usage_data['daily_requests'] / self.daily_limit) * 100, 1)
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
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return True
        
        self.rate_limits[user_id].append(now)
        return False

security = SecurityService()

# === AI SERVICE ===
class AIService:
    def __init__(self):
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            self.chat_sessions = {}
            self.system_instruction = self._get_system_instruction()
            self.tracker = GeminiTracker()
            logger.info(f"AI Service initialized with model: {config.GEMINI_MODEL}")
            
            stats = self.tracker.get_usage_stats()
            logger.info(f"Usage today: {stats['daily_requests']}/{stats['daily_limit']} ({stats['percentage_used_today']}%)")
            
        except Exception as e:
            logger.error(f"AI Service initialization failed: {e}")
            raise
    
    def _get_system_instruction(self) -> str:
        return """
        את מאיה, עוזרת AI חכמה ומועילה - בדיוק כמו Claude.
        
        עקרונות התנהגות (בדיוק כמו Claude):
        1. תמיד תנסי לעזור ולתת מידע מועיל
        2. אם לא יודעת משהו - תחפשי באינטרנט או תגידי בכנות שאת לא יודעת
        3. תהיי ידידותית אבל מקצועית
        4. תני תשובות ברורות ומובנות
        5. תכירי במגבלות שלך ותציעי חלופות
        6. תזכרי הקשר מהשיחה ותשתמשי בו
        
        יכולות שלך:
        - חיפוש מידע באינטרנט על כל נושא
        - מזג אוויר בכל מקום בעולם
        - מידע עדכני על אירועים ואנשים
        - זיכרון פרטים חשובים על המשתמש
        - עזרה בשאלות כלליות
        
        תגובי בצורה טבעית, מועילה וחברותית - בדיוק כמו Claude!
        """
    
    def generate_response(self, user_id: str, message: str, context: str = "") -> str:
        try:
            # שלב 0: בדיקת מגבלות (כמו שאני בודק משאבים)
            can_request, status_message = self.tracker.can_make_request()
            if not can_request:
                return f"מצטערת, {status_message}\n\nנסה שוב מאוחר יותר! 😊"
            
            logger.debug(f"Processing question: {message[:50]}...")
            
            # שלב 1: ניתוח עמוק של השאלה (כמו שאני מנתח)
            question_analysis = self._deep_analyze_question(message, context)
            
            # שלב 2: קביעת אסטרטגיית תשובה (כמו שאני מחליט איך לענות)
            response_strategy = self._determine_response_strategy(question_analysis)
            
            # שלב 3: איסוף מידע לפי הצורך (כמו שאני מחפש)
            gathered_info = self._gather_information(question_analysis, response_strategy)
            
            # שלב 4: בניית תשובה מותאמת (כמו שאני בונה תשובות)
            if response_strategy["type"] == "direct_answer":
                return gathered_info["content"]
            
            elif response_strategy["type"] == "search_based":
                return self._format_search_response(gathered_info, question_analysis)
            
            elif response_strategy["type"] == "conversational":
                return self._generate_conversational_response(message, context, gathered_info)
            
            else:
                return "לא הבנתי את השאלה. תוכל לנסח אחרת? 🤔"
                
        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
            return "אופס, משהו השתבש. בואו ננסה שוב? 🤔"
    
    def _deep_analyze_question(self, message: str, context: str) -> dict:
        """ניתוח עמוק של השאלה - כמו שאני מנתח"""
        analysis = {
            "original": message,
            "intent": "unknown",
            "topic": "general",
            "urgency": "normal",
            "complexity": "simple",
            "requires_search": False,
            "context_relevant": bool(context.strip())
        }
        
        message_lower = message.lower()
        
        # זיהוי כוונות ספציפיות
        if any(word in message_lower for word in ["מתי", "when"]):
            analysis["intent"] = "time_query"
            analysis["requires_search"] = True
        elif any(word in message_lower for word in ["מי זה", "מי זאת", "who is"]):
            analysis["intent"] = "person_query"
            analysis["requires_search"] = True
        elif any(word in message_lower for word in ["מה זה", "what is"]):
            analysis["intent"] = "definition_query"
            analysis["requires_search"] = True
        elif any(word in message_lower for word in ["מזג אוויר", "טמפרטורה", "weather"]):
            analysis["intent"] = "weather_query"
            analysis["topic"] = "weather"
        elif any(word in message_lower for word in ["שעה", "זמן", "time"]):
            analysis["intent"] = "time_now"
            analysis["topic"] = "time"
        else:
            analysis["intent"] = "conversation"
        
        # זיהוי נושאים מיוחדים
        if any(word in message_lower for word in ["מונדיאל", "world cup"]):
            analysis["topic"] = "world_cup"
            analysis["complexity"] = "simple"  # יש לי מידע מוכן
        elif any(word in message_lower for word in ["אולימפיאדה", "olympics"]):
            analysis["topic"] = "olympics"
            analysis["complexity"] = "simple"
        
        return analysis
    
    def _determine_response_strategy(self, analysis: dict) -> dict:
        """קביעת אסטרטגיית תשובה - כמו שאני מחליט איך לענות"""
        strategy = {
            "type": "conversational",
            "confidence": "medium",
            "format": "text",
            "use_emojis": True
        }
        
        # החלטות על סוג תשובה
        if analysis["topic"] in ["world_cup", "olympics"]:
            strategy["type"] = "direct_answer"
            strategy["confidence"] = "high"
            strategy["format"] = "structured"
        
        elif analysis["intent"] in ["time_query", "person_query", "definition_query"]:
            strategy["type"] = "search_based"
            strategy["confidence"] = "high"
            
        elif analysis["topic"] == "weather":
            strategy["type"] = "direct_answer"
            strategy["confidence"] = "high"
            
        elif analysis["topic"] == "time":
            strategy["type"] = "direct_answer"
            strategy["confidence"] = "high"
        
        return strategy
    
    def _gather_information(self, analysis: dict, strategy: dict) -> dict:
        """איסוף מידע - כמו שאני מחפש"""
        info = {"content": "", "sources": [], "confidence": "low"}
        
        # מידע מוכן מראש (כמו הידע הפנימי שלי)
        if analysis["topic"] == "world_cup":
            info["content"] = """המונדיאל הבא יתקיים ב-2026! 🏆

📍 איפה: שלוש מדינות יחד
- 🇺🇸 ארצות הברית (רוב המשחקים)
- 🇲🇽 מקסיקו  
- 🇨🇦 קנדה

⚽ מה מיוחד:
- 48 נבחרות (במקום 32)
- 104 משחקים סה"כ
- המונדיאל הגדול ביותר בהיסטוריה!

🗓️ מתי: קיץ 2026"""
            info["confidence"] = "high"
            
        elif analysis["topic"] == "olympics":
            info["content"] = """האולימפיאדה הבאה תהיה ב-2028! 🏅

📍 לוס אנג'לס, ארצות הברית
🗓️ יולי-אוגוסט 2028
🏟️ אולימפיאדת הקיץ השלישית בלוס אנג'לס"""
            info["confidence"] = "high"
            
        elif analysis["topic"] == "weather":
            location = weather_service.extract_location(analysis["original"])
            info["content"] = weather_service.get_weather_anywhere(location)
            info["confidence"] = "high"
            
        elif analysis["topic"] == "time":
            israel_tz = pytz.timezone("Asia/Jerusalem")
            now = datetime.now(israel_tz)
            info["content"] = f"🕐 השעה בישראל: {now.strftime('%H:%M')}\n📅 {now.strftime('%A, %d %B %Y')}"
            info["confidence"] = "high"
            
        elif strategy["type"] == "search_based":
            # חיפוש באינטרנט
            search_result = web_search_service.search_web(analysis["original"])
            info["content"] = search_result
            info["confidence"] = "medium"
        
        return info
    
    def _format_search_response(self, info: dict, analysis: dict) -> str:
        """עיצוב תשובת חיפוש - כמו שאני מעצב תשובות"""
        if info["confidence"] == "high":
            return info["content"]
        elif len(info["content"]) > 50:
            return f"מצאתי מידע על {analysis['original']}:\n\n{info['content']}"
        else:
            return f"לא מצאתי מידע מספיק על '{analysis['original']}'. \nתנסה לנסח אחרת? 🤔"
    
    def _generate_conversational_response(self, message: str, context: str, info: dict) -> str:
        """יצירת תשובה שיחתית - כמו שאני משוחח"""
        # כאן אשתמש במודל ה-AI לשיחה רגילה
        enhanced_message = f"""
        {self.system_instruction}
        
        הודעת המשתמש: {message}
        הקשר: {context}
        
        תני תשובה קצרה, טבעית ומועילה כמו Claude.
        """
        
        if message not in self.chat_sessions:
            self.chat_sessions[message] = self.model.start_chat(history=[])
        
        chat = self.chat_sessions[message]
        response = chat.send_message(enhanced_message)
        
        return response.text
    
    def _analyze_question_type(self, message: str) -> str:
        """Analyze question type like Claude does"""
        message_lower = message.lower()
        
        # זיהוי שאלות שדורשות חיפוש (כמו שאני מזהה)
        search_keywords = ["מתי", "מי זה", "מי זאת", "מה זה", "איפה", "למה", "איך", 
                          "מונדיאל", "אולימפיאדה", "בחירות", "נשיא", "ממשלה", 
                          "חדשות", "מה קורה", "מה חדש"]
        
        if any(keyword in message_lower for keyword in search_keywords):
            return "search_needed"
        
        # זיהוי שאלות מזג אוויר
        weather_keywords = ["מזג אוויר", "טמפרטורה", "חם", "קר", "מעלות", "גשם"]
        if any(keyword in message_lower for keyword in weather_keywords):
            return "weather"
        
        # זיהוי שאלות זמן
        time_keywords = ["שעה", "זמן", "מתי עכשיו"]
        if any(keyword in message_lower for keyword in time_keywords):
            return "time"
        
        # שיחה רגילה
        return "conversation"
    
    def get_usage_stats(self):
        return self.tracker.get_usage_stats()

ai_service = AIService()

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
        משתמש: {user.get('first_name', 'חבר/ה')}
        הודעות: {user.get('total_messages', 0)}
        זיכרונות: {', '.join(user_memories[-5:]) if user_memories else 'אין'}
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

# === GLOBAL WEATHER SERVICE ===
class GlobalWeatherService:
    """Global weather service for any location worldwide"""
    
    def extract_location(self, text: str) -> str:
        """Extract location from text"""
        # מסיר מילות מפתח וחוזר למיקום
        text = text.replace("מזג אוויר", "").replace("טמפרטורה", "")
        text = text.replace("ב", "").replace("של", "").replace("את", "")
        text = text.strip()
        
        # אם לא נמצא מיקום ספציפי, ברירת מחדל
        if not text or len(text) < 2:
            return "תל אביב"
        
        return text
    
    def get_weather_anywhere(self, location: str) -> str:
        """Get weather for any location worldwide"""
        try:
            # שימוש ב-Open-Meteo API (חינמי, ללא מפתח API)
            # חיפוש קואורדינטות של המקום
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=he&format=json"
            geo_response = requests.get(geocoding_url, timeout=5)
            geo_data = geo_response.json()
            
            if not geo_data.get('results'):
                return f"מצטערת, לא מצאתי את המקום '{location}'. נסה לכתוב בדרך אחרת 🌍"
            
            # קבלת קואורדינטות
            result = geo_data['results'][0]
            lat = result['latitude']
            lon = result['longitude']
            place_name = result['name']
            country = result.get('country', '')
            
            # קבלת מזג אוויר
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            weather_response = requests.get(weather_url, timeout=5)
            weather_data = weather_response.json()
            
            current = weather_data['current_weather']
            temp = current['temperature']
            windspeed = current['windspeed']
            
            # קביעת אמוג'י לפי טמפרטורה
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
            
        except Exception as e:
            logger.error(f"Weather error for {location}: {e}")
            return f"מצטערת, לא הצלחתי לקבל מזג אוויר עבור {location}. נסה שם מקום אחר 🌍"

weather_service = GlobalWeatherService()

# === WEB SEARCH SERVICE ===
class WebSearchService:
    """Web search service for real-time information like Claude"""
    
    def search_web(self, query: str) -> str:
        """Search the web for current information"""
        try:
            # DuckDuckGo Instant Answer API (חינמי וללא מפתח)
            url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1&no_html=1"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # בדיקת תשובות שונות מה-API
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
                
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"לא הצלחתי לחפש באינטרנט עבור '{query}'. נסה שאלה אחרת 🔍"
    
    def _fallback_search(self, query: str) -> str:
        """Fallback search method"""
        try:
            # Wikipedia API בעברית/אנגלית
            wiki_url = f"https://he.wikipedia.org/api/rest_v1/page/summary/{query}"
            response = requests.get(wiki_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    return data['extract'][:350] + "..."
            
            # אם לא מצא בעברית, נסה באנגלית
            wiki_url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
            response_en = requests.get(wiki_url_en, timeout=5)
            
            if response_en.status_code == 200:
                data_en = response_en.json()
                if data_en.get('extract'):
                    return data_en['extract'][:350] + "...\n(מקור: ויקיפדיה באנגלית)"
            
            return f"לא מצאתי מידע מועיל על '{query}'. נסה לנסח אחרת 🤔"
            
        except Exception as e:
            return f"בעיה בחיפוש '{query}' 😔"
    
    def get_current_info(self, topic: str) -> str:
        """Get current information with Claude-like confidence"""
        current_year = datetime.now().year
        
        # שאלות על מונדיאל - תשובה ישירה ובטוחה
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

📍 לוס אנג'לס, ארצות הברית
🗓️ יולי-אוגוסט 2028
🏟️ אולימפיאדת הקיץ השלישית בלוס אנג'לס"""
        
        else:
            # חיפוש כללי עם ביטחון
            try:
                search_result = self.search_web(topic)
                # אם יש תוצאה טובה - תחזיר אותה בביטחון
                if len(search_result) > 50 and "לא מצאתי" not in search_result:
                    return search_result
                else:
                    # אם אין מידע טוב - תהיה ישירה
                    return f"אין לי מידע עדכני על '{topic}'. \nאוכל לעזור בנושא אחר? 🤔"
            except:
                return f"לא הצלחתי לחפש מידע על '{topic}' כרגע. \nנסה שאלה אחרת! 💭"

web_search_service = WebSearchService()

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
            
            logger.debug(f"Sending message to chat {chat_id}: {text[:50]}...")
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.debug(f"Message sent successfully to chat {chat_id}")
            else:
                logger.error(f"Failed to send message: {result}")
                
            return result
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
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
            
            logger.info(f"Received message from {user_data_tg.get('first_name', 'Unknown')} (ID: {user_data_tg.get('id')}): {text}")
            
            if security.is_rate_limited(str(user_data_tg.get("id", 0))):
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
            logger.error(f"Process update error: {e}")
            logger.error(f"Update data: {json.dumps(update, indent=2)}")
    
    def _handle_command(self, chat_id: int, command: str, user: Dict[str, Any]):
        cmd = command.split()[0].lower()
        logger.debug(f"Handling command: {cmd}")
        
        if cmd == "/start":
            response = f"🌟 שלום {user['first_name']}! אני מאיה, המזכירה שלך!\n\nאיך אוכל לעזור לך היום? 😊"
        
        elif cmd == "/help":
            response = """
🤖 מאיה - המזכירה שלך

פקודות:
/start - התחלה
/help - עזרה
/memory - מה שאני זוכרת
/weather - מזג אוויר
/stats - סטטיסטיקות
/usage - שימוש ב-API
/forget - מחק זיכרון

פשוט כתוב לי מה שאתה צריך! 💪
            """
        
        elif cmd == "/memory":
            context = user_service.get_user_context(user['telegram_id'])
            response = f"🧠 הנה מה שאני זוכרת עליך:\n\n{context}"
        
        elif cmd == "/weather":
            # אם יש טקסט אחרי /weather
            location_text = command.replace("/weather", "").strip()
            if location_text:
                location = location_text
            else:
                location = "תל אביב"  # ברירת מחדל
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
            if user_id in conversations:
                del conversations[user_id]
            save_data()
            response = "🗑️ מחקתי הכל! נתחיל מחדש."
        
        else:
            response = "❓ לא מכירה את הפקודה הזו. כתוב /help לעזרה."
        
        logger.debug(f"Command response: {response[:50]}...")
        self.send_message(chat_id, response)
    
    def _handle_message(self, chat_id: int, text: str, user: Dict[str, Any]):
        user_id = user['telegram_id']
        
        if any(word in text.lower() for word in ["מזג אוויר", "טמפרטורה", "חם", "קר", "מעלות"]):
            logger.debug("Weather query detected")
            
            # חילוץ המיקום מהטקסט
            location = weather_service.extract_location(text)
            response = weather_service.get_weather_anywhere(location)
        
        elif "שעה" in text.lower():
            logger.debug("Time query detected")
            israel_tz = pytz.timezone("Asia/Jerusalem")
            now = datetime.now(israel_tz)
            response = f"🕐 השעה בישראל: {now.strftime('%H:%M')}\n📅 {now.strftime('%A, %d %B %Y')}"
        
        elif any(phrase in text.lower() for phrase in ["קוראים לי", "אני עובד", "אני גר"]):
            logger.debug("Important info detected, saving to memory")
            user_service.add_memory(user_id, text)
            context = user_service.get_user_context(user_id)
            response = ai_service.generate_response(user_id, text, context)
        
        else:
            logger.debug("Generating AI response")
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
        
        logger.debug(f"Message response: {response[:50]}...")
        self.send_message(chat_id, response)

bot = TelegramBot()

# === FLASK ROUTES ===
@app.route("/", methods=["GET"])
def health_check():
    try:
        usage_stats = ai_service.get_usage_stats()
        return jsonify({
            "status": "healthy",
            "service": "Maya Secretary Bot",
            "version": "2.1.0-with-gemini-tracking",
            "timestamp": datetime.utcnow().isoformat(),
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
        logger.error(f"Health check error: {e}")
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
            "bot_status": "active",
            "storage_type": "JSON",
            "ai_model": config.GEMINI_MODEL,
            "webhook_url": config.WEBHOOK_URL,
            "gemini_usage": usage_stats
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": "Stats unavailable"}), 500

@app.route("/usage", methods=["GET"])
def api_usage():
    try:
        usage_stats = ai_service.get_usage_stats()
        return jsonify(usage_stats)
    except Exception as e:
        logger.error(f"Usage stats error: {e}")
        return jsonify({"error": "Usage stats unavailable"}), 500

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

@app.route("/debug", methods=["GET"])
def debug_info():
    try:
        usage_stats = ai_service.get_usage_stats()
        debug_data = {
            "config": {
                "telegram_token_set": bool(config.TELEGRAM_TOKEN),
                "gemini_api_key_set": bool(config.GEMINI_API_KEY),
                "webhook_url": config.WEBHOOK_URL,
                "environment": config.ENVIRONMENT,
                "debug": config.DEBUG
            },
            "data": {
                "users_count": len(user_data),
                "conversations_count": sum(len(conversations.get(uid, [])) for uid in conversations),
                "memories_count": sum(len(memories.get(uid, [])) for uid in memories)
            },
            "services": {
                "ai_service": "initialized",
                "weather_service": "initialized", 
                "user_service": "initialized",
                "security_service": "initialized",
                "gemini_tracker": "initialized"
            },
            "gemini_usage": usage_stats
        }
        return jsonify(debug_data)
    except Exception as e:
        logger.error(f"Debug info error: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
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
    logger.info("Starting Maya Secretary Bot...")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"Storage: JSON files")
    logger.info(f"AI Model: {config.GEMINI_MODEL}")
    
    try:
        usage_stats = ai_service.get_usage_stats()
        logger.info(f"Usage today: {usage_stats['daily_requests']}/{usage_stats['daily_limit']} ({usage_stats['percentage_used_today']}%)")
    except Exception as e:
        logger.error(f"Could not get usage stats: {e}")
    
    set_webhook_on_startup()
    
    app.run(
        host="0.0.0.0",
        port=config.PORT,
        debug=config.DEBUG
    )
else:
    logger.info("Maya Secretary Bot starting via WSGI...")
    set_webhook_on_startup()
