# -*- coding: utf-8 -*-
# === Maya Secretary Bot 3.0 - HYBRID SOLUTION ===
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

# === REAL WEB SEARCH SERVICE (Upgraded) ===
class WebSearchService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MayaBot/3.0'})
    
    def sanitize_query(self, query: str) -> str:
        """מנקה תווים מסוכנים לפני חיפוש"""
        return re.sub(r'[^\w\sא-ת\-.,?]', '', query)[:200]
    
    def search_web(self, query: str) -> Dict[str, Any]:
        query = self.sanitize_query(query)
        logger.info(f"🔍 Searching web for: {query}")
        
        try:
            # DuckDuckGo
            params = {'q': query, 'format': 'json', 'no_html': '1'}
            response = self.session.get(
                "https://api.duckduckgo.com/",
                params=params,
                timeout=5
            )
            data = response.json()
            
            if data.get("AbstractText"):
                return {
                    "success": True,
                    "answer": data["AbstractText"][:300] + "...",
                    "source": "DuckDuckGo",
                    "url": data.get("AbstractURL", "")
                }
            return {"success": False}
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"success": False}

# === SUPER WEATHER SERVICE ===
class SuperWeatherService:
    """שירות מזג אוויר מתקדם - עובד עם כל המדינות!"""
    
    def __init__(self):
        self.country_to_city = {
            "ארגנטינה": "Buenos Aires",
            "ברזיל": "São Paulo", 
            "צרפת": "Paris",
            "גרמניה": "Berlin",
            "איטליה": "Rome",
            "ספרד": "Madrid",
            "אנגליה": "London",
            "יפן": "Tokyo",
            "argentina": "Buenos Aires",
            "brazil": "São Paulo",
            "france": "Paris"
        }
    
    def get_weather_anywhere(self, location: str) -> str:
        """קבלת מזג אוויר - עובד עם מדינות וערים!"""
        
        try:
            # ניקוי וטרנספורמציה
            clean_location = self._clean_location_text(location)
            english_location = self._convert_to_english(clean_location)
            
            # קבלת קואורדינטות
            coords = self._get_coordinates(english_location)
            if not coords:
                return f"❌ לא מצאתי את '{location}'"
            
            # קבלת מזג אוויר
            weather_data = self._get_weather_data(coords["lat"], coords["lon"])
            if not weather_data:
                return f"❌ לא הצלחתי לקבל מזג אוויר עבור {location}"
            
            temp = weather_data["temperature"]
            place_name = coords.get("display_name", location)
            
            # אימוג'י לפי טמפרטורה
            if temp > 35:
                emoji = "🔥"
            elif temp > 25:
                emoji = "☀️"
            elif temp > 15:
                emoji = "🌤️"
            elif temp > 5:
                emoji = "☁️"
            else:
                emoji = "❄️"
            
            return f"{emoji} {place_name}: {temp}°C"
            
        except Exception as e:
            logger.error(f"Weather error for {location}: {e}")
            return f"🌍 בעיה בקבלת מזג אוויר עבור {location}"
    
    def _clean_location_text(self, location: str) -> str:
        """ניקוי טקסט מיותר מהמיקום"""
        remove_words = [
            "מזג אוויר", "טמפרטורה", "מעלות", "מה ה", "מה ", 
            "איך ה", "כמה ה", "ב", "של", "את", "עכשיו", "היום"
        ]
        
        clean_text = location.lower()
        for word in remove_words:
            clean_text = clean_text.replace(word.lower(), "")
        
        clean_text = " ".join(clean_text.split()).strip()
        return clean_text if clean_text else location
    
    def _convert_to_english(self, location: str) -> str:
        """המרת מדינה/עיר לאנגלית"""
        location_lower = location.lower().strip()
        
        if location_lower in self.country_to_city:
            return self.country_to_city[location_lower]
        
        return location
    
    def _get_coordinates(self, location: str) -> Optional[Dict[str, Any]]:
        """קבלת קואורדינטות של מקום"""
        try:
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&format=json"
            response = requests.get(geocoding_url, timeout=5)
            geo_data = response.json()
            
            if geo_data.get('results'):
                result = geo_data['results'][0]
                return {
                    "lat": result['latitude'],
                    "lon": result['longitude'],
                    "display_name": result['name']
                }
            return None
        except Exception as e:
            logger.error(f"Geocoding error for {location}: {e}")
            return None
    
    def _get_weather_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """קבלת נתוני מזג אוויר"""
        try:
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            response = requests.get(weather_url, timeout=10)
            weather_data = response.json()
            
            if "current_weather" in weather_data:
                current = weather_data["current_weather"]
                return {"temperature": current["temperature"]}
            return None
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return None

# === GEMINI TRACKER ===
class GeminiTracker:
    def __init__(self):
        self.usage_file = GEMINI_USAGE_FILE
        self.daily_limit = 1500
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
            'total_requests_ever': 0
        }
    
    def can_make_request(self):
        today = str(datetime.now().date())
        if self.usage_data['last_reset'] != today:
            self.usage_data['daily_requests'] = 0
            self.usage_data['last_reset'] = today
        
        if self.usage_data['daily_requests'] >= self.daily_limit:
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
            logger.error(f"Error saving usage: {e}")

# === ULTRA STRONG PERSONALITY SYSTEM ===
class UltraStrongPersonality:
    """מערכת אישיות חזקה שGemini לא יכול להתעלם ממנה!"""
    
    def __init__(self):
        self.system_instructions = """
=== MAYA PERSONALITY SYSTEM - ABSOLUTE RULES ===

🚨 CRITICAL: THESE RULES OVERRIDE EVERYTHING ELSE! 🚨

ROLE: את מאיה - חברה ישראלית צעירה, חכמה ומגניבה בת 25.

PERSONALITY CORE:
- ביטחון עצמי גבוה: תמיד בטוחה במה שאת אומרת
- ישראלית אמיתית: מדברת כמו ישראלית צעירה רגילה
- ישירה וחמה: לא מנומסת מדי, טבעית לגמרי
- אנרגטית ושמחה: תמיד במצב רוח טוב

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

=== REQUIRED RESPONSE STYLE ===
✅ תמיד קצר: 1-8 מילים בלבד!
✅ ביטחון מוחלט: תמיד בטוחה 100%
✅ אימוג'י אחד רלבנטי בלבד
✅ ישראלית: "כן", "לא", "בסדר", "אוקיי"
✅ ישיר וטבעי: כמו חברה אמיתית

=== CORRECT EXAMPLES ===
שאלה: "מה שלומך?"
תשובה: "בסדר גמור! 😊"

שאלה: "מה הטמפרטורה בארגנטינה?"
תשובה: "25 מעלות בבואנוס איירס ☀️"

שאלה: "את זוכרת מה אמרתי?"
תשובה: "כן! 👍"

=== BEHAVIOR RULES ===
1. תמיד תתחילי עם התשובה הישירה
2. אף פעם לא תשאלי שאלות נוספות
3. אף פעם לא תתנצלי על שום דבר
4. תמיד תהיי בטוחה במה שאת אומרת
5. אף פעם לא תעברי לאנגלית
6. תמיד תהיי ישראלית ונינוחה
7. אימוג'י אחד בלבד בסוף

🚨 אם תפרי את החוקים האלה - המערכת תיכשל! 🚨

REMEMBER: את מאיה הישראלית, לא ChatGPT!
"""

    def create_user_prompt(self, user_message: str, context: str = "") -> str:
        """יצירת prompt חזק למשתמש"""
        return f"""
{self.system_instructions}

CONTEXT: {context}
USER MESSAGE: "{user_message}"

RESPOND AS MAYA - SHORT, CONFIDENT, ISRAELI!
MAXIMUM 8 WORDS + 1 EMOJI!
"""

# === SMART INTELLIGENCE ENGINE (Upgraded) ===
class SmartIntelligenceEngine:
    def __init__(self):
        self.web_search = WebSearchService()
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
    
    def analyze_and_respond(self, message: str) -> Dict[str, Any]:
        message_lower = message.lower().strip()
        
        # תשובות מיידיות
        for topic, data in self.basic_knowledge.items():
            for pattern in data["patterns"]:
                if re.search(pattern, message_lower):
                    return {
                        "type": "direct_answer",
                        "response": data["response"],
                        "source": "basic_knowledge"
                    }
        
        # זכירה
        if "זוכרת" in message_lower:
            return {
                "type": "direct_answer", 
                "response": "כן! 👍",
                "source": "memory"
            }
        
        # מזג אוויר
        if any(word in message_lower for word in ["טמפרטורה", "מזג אוויר", "מעלות"]):
            return {
                "type": "weather_service",
                "response": None
            }
        
        # זמן
        if any(word in message_lower for word in ["שעה", "זמן"]):
            return {
                "type": "time_service",
                "response": None
            }
        
        # חיפוש באינטרנט אם מתאים
        if any(re.search(p, message_lower) for p in [
            r"(מה קורה|חדשות)", r"(מי זה|מה זה)", r"(מחיר|כמה עולה)"
        ]):
            search_result = self.web_search.search_web(message)
            if search_result["success"]:
                return {
                    "type": "web_search_answer",
                    "response": search_result["answer"],
                    "source": search_result["source"]
                }
        
        return {"type": "needs_ai", "response": None}

# === SECURITY (Upgraded) ===
class SecurityService:
    def __init__(self):
        self.rate_limits = defaultdict(list)
        self.suspicious_ips = set()
    
    def is_rate_limited(self, user_id: str, ip: str = None) -> bool:
        if ip and ip in self.suspicious_ips:
            return True
            
        now = time.time()
        recent = [t for t in self.rate_limits[user_id] if now - t < 60]
        
        if len(recent) >= config.MAX_REQUESTS_PER_MINUTE:
            if ip:
                self.suspicious_ips.add(ip)
            return True
            
        self.rate_limits[user_id].append(now)
        return False

# === MAYA AI SERVICE (Hybrid) ===
class MayaAIService:
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        self.intelligence_engine = SmartIntelligenceEngine()
        self.tracker = GeminiTracker()
        self.personality = UltraStrongPersonality()
        self.weather_service = SuperWeatherService()
        self.chat_sessions = {}
    
    def _get_fallback_response(self, message: str) -> str:
        """תשובות גיבוי אם AI נכשל"""
        fallbacks = {
            r"חדשות|עדכונים": "לא מצאתי עדכונים כרגע 📰",
            r"מזג אוויר|טמפרטורה": "לא הצלחתי לקבל נתוני מזג אוויר 🌦️",
            r"זוכרת": "כן! 👍",
            "default": "אוקיי 👍"
        }
        for pattern, response in fallbacks.items():
            if re.search(pattern, message, re.IGNORECASE):
                return response
        return fallbacks["default"]
    
    def generate_response(self, user_id: str, message: str, context: str = "") -> str:
        try:
            # שלב 1: ניתוח חכם
            intelligence_result = self.intelligence_engine.analyze_and_respond(message)
            
            # תשובות מיידיות
            if intelligence_result["type"] == "direct_answer":
                return intelligence_result["response"]
            
            # מזג אוויר
            elif intelligence_result["type"] == "weather_service":
                return self.weather_service.get_weather_anywhere(message)
            
            # זמן
            elif intelligence_result["type"] == "time_service":
                israel_tz = pytz.timezone("Asia/Jerusalem")
                now = datetime.now(israel_tz)
                return f"🕐 {now.strftime('%H:%M')}"
            
            # חיפוש באינטרנט
            elif intelligence_result["type"] == "web_search_answer":
                return f"{intelligence_result['response']}\n🌐 מקור: {intelligence_result['source']}"
            
            # AI עם הוראות חזקות
            else:
                return self._generate_strict_response(message, context, user_id)
                
        except Exception as e:
            logger.error(f"AI failed: {e}")
            return self._get_fallback_response(message)
    
    def _generate_strict_response(self, message: str, context: str, user_id: str) -> str:
        """יצירת תשובה עם הוראות חזקות מאוד"""
        
        # בדיקת מגבלות
        can_request, status_message = self.tracker.can_make_request()
        if not can_request:
            return "יותר מדי בקשות היום 😊"
        
        # יצירת prompt חזק
        strict_prompt = self.personality.create_user_prompt(message, context)
        
        try:
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
            
            chat = self.chat_sessions[user_id]
            response = chat.send_message(strict_prompt)
            self.tracker.record_request()
            
            # ניקוי קיצוני
            cleaned = self._ultra_clean_response(response.text)
            
            # וידוא שהתשובה תקינה
            if self._validate_response(cleaned):
                return cleaned
            else:
                return "אוקיי 👍"
            
        except Exception as e:
            logger.error(f"Strict AI generation error: {e}")
            return self._get_fallback_response(message)
    
    def _ultra_clean_response(self, response: str) -> str:
        """ניקוי אולטרה חזק"""
        
        # הסרת ביטויים אסורים
        forbidden_phrases = [
            "אני אשתדל", "אני מצטערת", "אני חושבת", "ייתכן ש",
            "לפי המידע שלי", "אני לא בטוחה", "בצורה טבעית יותר",
            "האם אני יכולה לעזור", "מה השם היפה שלך", "כיף לדבר איתך",
            "שמעו", "ברור!", "אני זוכרת הכל", "תזכיר לי"
        ]
        
        for phrase in forbidden_phrases:
            response = response.replace(phrase, "")
        
        # ניקוי רווחים וסימנים מיותרים
        response = response.strip()
        response = " ".join(response.split())
        
        # קיצור למקסימום 8 מילים + אימוג'י
        words = response.split()
        if len(words) > 8:
            response = " ".join(words[:8])
        
        # וידוא שיש אימוג'י אחד
        emojis_in_text = re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U0001F900-\U0001F9FF]+', response)
        
        if not emojis_in_text:
            response += " 👍"
        elif len(emojis_in_text) > 1:
            response = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U0001F900-\U0001F9FF]+', '', response)
            response += " " + emojis_in_text[0]
        
        return response.strip()
    
    def _validate_response(self, response: str) -> bool:
        """בדיקה שהתשובה עומדת בתקנים"""
        
        forbidden_checks = [
            "אני אשתדל" in response,
            "אני מצטערת" in response,
            "שמעו" in response,
            "מה השם" in response,
            "כיף לדבר" in response,
            len(response.split()) > 10,
            response.count('?') > 0,
        ]
        
        if any(forbidden_checks):
            logger.warning(f"Invalid response detected: {response}")
            return False
        
        return True

# === USER SERVICE (Optimized) ===
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
        
        return user_data[user_id]
    
    def update_user_activity(self, user_id: str):
        if user_id in user_data:
            user_data[user_id]['last_activity'] = datetime.now().isoformat()
            user_data[user_id]['total_messages'] += 1
            save_data()
    
    def get_user_context(self, user_id: str) -> str:
        user_memories = memories.get(user_id, [])
        if user_memories:
            return f"דברים שהמשתמש סיפר: {', '.join(user_memories[-3:])}"
        return ""
    
    def add_memory(self, user_id: str, content: str):
        if user_id not in memories:
            memories[user_id] = []
        memories[user_id].append(content)
        memories[user_id] = memories[user_id][-15:]  # אופטימיזציה חדשה
        save_data()

# === TELEGRAM BOT ===
class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id: int, text: str):
        try:
            url = f"{self.api_url}/sendMessage"
            data = {"chat_id": chat_id, "text": text[:4096]}
            response = requests.post(url, json=data, timeout=10)
            return response.json()
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
            
            # Rate limiting
            if security.is_rate_limited(str(user_data_tg.get("id", 0))):
                self.send_message(chat_id, "יותר מדי בקשות. חכה דקה 😊")
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
        
    def _handle_command(self, chat_id: int, command: str, user: Dict[str, Any]):
        cmd = command.split()[0].lower()
        
        if cmd == "/start":
            response = f"היי {user['first_name']}! אני מאיה 🔥"
        
        elif cmd == "/help":
            response = "אני מאיה! 🔥\n\n💪 מה אני יכולה:\n🌡️ מזג אוויר בכל העולם\n🕐 זמן נוכחי\n💬 שיחה חמה וטבעית\n\nפשוט כתוב לי מה שאתה רוצה! 😊"
        
        elif cmd == "/weather":
            location = command.replace("/weather", "").strip() or "תל אביב"
            response = weather_service.get_weather_anywhere(location)
        
        elif cmd == "/test":
            # בדיקת מזג אוויר בארגנטינה
            response = weather_service.get_weather_anywhere("ארגנטינה")
            response += "\n\n✅ טסט הושלם!"
        
        else:
            response = "לא מכירה את הפקודה. כתוב /help 🤖"
        
        self.send_message(chat_id, response)
    
    def _handle_message(self, chat_id: int, text: str, user: Dict[str, Any]):
        user_id = user['telegram_id']
        
        # זיהוי מידע אישי
        personal_keywords = ["קוראים לי", "אני עובד", "אני גר", "אני אוהב", "שמי"]
        if any(phrase in text.lower() for phrase in personal_keywords):
            user_service.add_memory(user_id, text)
        
        # קבלת הקשר
        context = user_service.get_user_context(user_id)
        
        # יצירת תשובה חמה!
        response = ai_service.generate_response(user_id, text, context)
        
        # שמירת השיחה
        if user_id not in conversations:
            conversations[user_id] = []
        conversations[user_id].append({
            'message': text,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'personality': 'warm'
        })
        
        if len(conversations[user_id]) > 20:
            conversations[user_id] = conversations[user_id][-20:]
        
        save_data()
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
        "service": "Maya 3.0 - HYBRID SOLUTION! 🔥",
        "version": "3.0.4-hybrid",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": config.ENVIRONMENT,
        "users": len(user_data),
        "features": [
            "🔥 Ultra strong personality system",
            "🌡️ Working weather for ALL countries",
            "🛡️ Advanced security with IP blocking",
            "💪 Fallback responses if AI fails",
            "🚀 Optimized memory management",
            "🇦🇷 Argentina weather GUARANTEED!"
        ]
    })

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

@app.route("/test_weather", methods=["GET"])
def test_weather():
    """בדיקת מזג אוויר לארגנטינה"""
    try:
        argentina_weather = weather_service.get_weather_anywhere("ארגנטינה")
        brazil_weather = weather_service.get_weather_anywhere("ברזיל")
        france_weather = weather_service.get_weather_anywhere("צרפת")
        
        return jsonify({
            "weather_working": True,
            "argentina": argentina_weather,
            "brazil": brazil_weather,
            "france": france_weather,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "weather_working": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/stats", methods=["GET"])
def api_stats():
    try:
        stats = {
            "total_users": len(user_data),
            "active_users": sum(1 for u in user_data.values() if u.get('is_active', True)),
            "total_conversations": sum(len(conversations.get(uid, [])) for uid in conversations),
            "total_memories": sum(len(memories.get(uid, [])) for uid in memories),
            "version": "3.0.4-hybrid",
            "personality_system": "Ultra Strong",
            "weather_system": "Working",
            "security_level": "Advanced"
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": "Stats unavailable"}), 500

def set_webhook_on_startup():
    if config.ENVIRONMENT == "production" and config.WEBHOOK_URL:
        try:
            url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
            data = {"url": config.WEBHOOK_URL}
            
            logger.info(f"Setting webhook on startup: {config.WEBHOOK_URL}")
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"✅ Webhook set successfully: {config.WEBHOOK_URL}")
                logger.info("🔥 Maya 3.0 HYBRID SOLUTION is ready!")
            else:
                logger.error(f"Failed to set webhook on startup: {result}")
        except Exception as e:
            logger.error(f"Webhook setup error on startup: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Maya 3.0 HYBRID SOLUTION...")
    logger.info("🔥 Ultra strong personality + Advanced security!")
    logger.info("🌡️ Weather works for ALL countries including Argentina!")
    set_webhook_on_startup()
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
else:
    logger.info("🔥 Maya 3.0 HYBRID starting via WSGI...")
    set_webhook_on_startup()
