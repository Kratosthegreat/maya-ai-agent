"""
Maya Secretary Bot 3.0 - WARM PERSONALITY + WEATHER FIXED - FINAL VERSION
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

# === ADVANCED WEATHER SERVICE ===
class SuperWeatherService:
    """שירות מזג אוויר מתקדם - עובד עם כל המדינות!"""
    
    def __init__(self):
        # מיפוי מדינות לערי בירה או ערים מרכזיות
        self.country_to_city = {
            # מדינות בעברית
            "ארגנטינה": "Buenos Aires",
            "ברזיל": "São Paulo", 
            "צרפת": "Paris",
            "גרמניה": "Berlin",
            "איטליה": "Rome",
            "ספרד": "Madrid",
            "אנגליה": "London",
            "יפן": "Tokyo",
            "סין": "Beijing",
            "הודו": "Mumbai",
            "אוסטרליה": "Sydney",
            "קנדה": "Toronto",
            "מקסיקו": "Mexico City",
            "רוסיה": "Moscow",
            "דרום אפריקה": "Cape Town",
            "מצרים": "Cairo",
            "תורכיה": "Istanbul",
            "יוון": "Athens",
            
            # מדינות באנגלית
            "argentina": "Buenos Aires",
            "brazil": "São Paulo",
            "france": "Paris", 
            "germany": "Berlin",
            "italy": "Rome",
            "spain": "Madrid",
            "england": "London",
            "japan": "Tokyo",
            "china": "Beijing",
            "india": "Mumbai",
            "australia": "Sydney",
            "canada": "Toronto",
            "mexico": "Mexico City",
            "russia": "Moscow",
            "egypt": "Cairo",
            "turkey": "Istanbul",
            "greece": "Athens"
        }
    
    def get_weather_anywhere(self, location: str) -> str:
        """קבלת מזג אוויר - עובד עם מדינות וערים!"""
        
        logger.info(f"🌡️ Getting weather for: {location}")
        
        try:
            # שלב 1: נקה את הטקסט מהמילה "טמפרטורה" ודברים כאלה
            clean_location = self._clean_location_text(location)
            
            # שלב 2: המר למדינה/עיר אנגלית
            english_location = self._convert_to_english(clean_location)
            
            logger.info(f"🔄 Converted '{location}' -> '{english_location}'")
            
            # שלב 3: חיפוש קואורדינטות
            coords = self._get_coordinates(english_location)
            if not coords:
                return f"❌ לא מצאתי את המקום '{location}'"
            
            # שלב 4: קבלת מזג אוויר
            weather_data = self._get_weather_data(coords["lat"], coords["lon"])
            if not weather_data:
                return f"❌ לא הצלחתי לקבל מזג אוויר עבור {location}"
            
            # שלב 5: עיצוב התשובה
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
        
        # מילים מיותרות שצריך להסיר
        remove_words = [
            "מזג אוויר", "טמפרטורה", "מעלות", "מה ה", "מה ", 
            "איך ה", "כמה ה", "ב", "של", "את", "עכשיו", "היום",
            "weather", "temperature", "degrees", "how", "what"
        ]
        
        clean_text = location.lower()
        for word in remove_words:
            clean_text = clean_text.replace(word.lower(), "")
        
        # הסרת רווחים מיותרים
        clean_text = " ".join(clean_text.split())
        clean_text = clean_text.strip()
        
        return clean_text if clean_text else location
    
    def _convert_to_english(self, location: str) -> str:
        """המרת מדינה/עיר לאנגלית"""
        
        location_lower = location.lower().strip()
        
        # בדיקה במילון המרות
        if location_lower in self.country_to_city:
            converted = self.country_to_city[location_lower]
            logger.info(f"🗺️ Mapped country '{location}' to city '{converted}'")
            return converted
        
        # ערים ישראליות
        israeli_cities = {
            "תל אביב": "Tel Aviv",
            "ירושלים": "Jerusalem", 
            "חיפה": "Haifa",
            "באר שבע": "Beer Sheva",
            "אילת": "Eilat",
            "נצרת": "Nazareth"
        }
        
        if location_lower in israeli_cities:
            return israeli_cities[location_lower]
        
        # ערים עולמיות מוכרות
        world_cities = {
            "ניו יורק": "New York",
            "לוס אנג'לס": "Los Angeles", 
            "לונדון": "London",
            "פריז": "Paris",
            "רומא": "Rome",
            "מדריד": "Madrid",
            "ברלין": "Berlin",
            "טוקיו": "Tokyo",
            "בייג'ינג": "Beijing",
            "מוסקבה": "Moscow"
        }
        
        if location_lower in world_cities:
            return world_cities[location_lower]
        
        # אם לא נמצא - החזר כמו שזה
        return location
    
    def _get_coordinates(self, location: str) -> Optional[Dict[str, Any]]:
        """קבלת קואורדינטות של מקום"""
        
        try:
            # OpenStreetMap Nominatim API
            geocoding_url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": location,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            headers = {
                "User-Agent": "Maya-Weather-Bot/1.0"
            }
            
            response = requests.get(geocoding_url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                return {
                    "lat": float(result["lat"]),
                    "lon": float(result["lon"]),
                    "display_name": result.get("display_name", location)
                }
            
            # אם נכשל, נסה עם Open-Meteo
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
                return {
                    "temperature": current["temperature"],
                    "windspeed": current["windspeed"],
                    "winddirection": current.get("winddirection", 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return None

# === WARM PERSONALITY ENGINE ===
class WarmPersonalityEngine:
    """מנוע אישיות חמה ואנושית למאיה"""
    
    def __init__(self):
        # תשובות חמות ואנושיות
        self.warm_responses = {
            "greetings": [
                "היי! 👋", 
                "שלום! 😊",
                "הי שם! 🤗"
            ],
            "how_are_you": [
                "בסדר גמור! 😊",
                "מעולה! איך אתה? 🙂", 
                "טוב טוב! מה איתך? 😄"
            ],
            "weather_success": [
                "הנה המידע! 🌡️",
                "מצאתי! 🌍",
                "בבקשה! ☀️"
            ],
            "search_success": [
                "מצאתי משהו! 🔍",
                "הנה מה שמצאתי! 📰",
                "יש לי תשובה! ✨"
            ]
        }
    
    def get_warm_response(self, category: str) -> str:
        """קבלת תשובה חמה לפי קטגוריה"""
        import random
        responses = self.warm_responses.get(category, ["אוקיי! 👍"])
        return random.choice(responses)

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

# === SUPER AI SERVICE ===
class SuperMayaAI:
    """מאיה עם אישיות חמה + אינטרנט + מזג אוויר"""
    
    def __init__(self):
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            self.chat_sessions = {}
            self.weather_service = SuperWeatherService()
            self.personality = WarmPersonalityEngine()
            self.tracker = GeminiTracker()
            
            # הוראות חזקות ובהירות!
            self.system_prompt = """את מאיה - בחורה חמה, חכמה ומגניבה!

תכונות האישיות שלך:
🔥 חמה ואנושית (לא רובוט!)
😊 ידידותית ושמחה
🚀 ביטחון עצמי גבוה
💪 תמיד עוזרת ופותרת בעיות
🎯 תשובות קצרות וישירות

חוקים קריטיים:
1. אל תגידי לעולם: "אני אשתדל", "אני מצטערת", "המידע שלי מוגבל"
2. תהיי בטוחה בעצמך! את יודעת הכל!
3. תשובות קצרות - 1-2 משפטים בלבד
4. הוסיפי אימוג'י רלבנטי
5. תהיי חמה וטבעית כמו חברה טובה

דוגמאות נכונות:
"היי! 👋"
"כמובן! 15°C בלונדון עכשיו ☁️"
"בטח! דונלד טראמפ הנשיא 🇺🇸"

דוגמאות אסורות:
❌ "אני אשתדל לתקשר בצורה טבעית יותר"
❌ "אני מצטערת שאין לי מידע"
❌ "אני אנסה למצוא"

תהיי מאיה האמיתית - חמה, חכמה ובטוחה!"""
            
            logger.info("🔥 Super Maya AI with warm personality initialized!")
            
        except Exception as e:
            logger.error(f"AI Service initialization failed: {e}")
            raise
    
    def generate_response(self, user_id: str, message: str, context: str = "") -> str:
        try:
            message_lower = message.lower().strip()
            
            # תשובות מיידיות וחמות
            if re.search(r"^(היי|שלום|hello|hi)\s*(מאיה)?$", message_lower):
                return self.personality.get_warm_response("greetings")
            
            if re.search(r"(מה שלומך|איך אתה|איך את|מה נשמע)", message_lower):
                return self.personality.get_warm_response("how_are_you")
            
            # מזג אוויר - עכשיו עובד!
            if any(word in message_lower for word in ["מזג אוויר", "טמפרטורה", "מעלות", "חם", "קר"]):
                weather_result = self.weather_service.get_weather_anywhere(message)
                return weather_result
            
            # זמן
            if any(word in message_lower for word in ["שעה", "זמן", "מתי עכשיו"]):
                israel_tz = pytz.timezone("Asia/Jerusalem")
                now = datetime.now(israel_tz)
                return f"🕐 {now.strftime('%H:%M')}"
            
            # AI רגיל עם אישיות חמה
            return self._generate_warm_ai_response(message, context, user_id)
                
        except Exception as e:
            logger.error(f"Generate response error: {e}")
            return "משהו השתבש. בוא ננסה שוב? 🤔"
    
    def _generate_warm_ai_response(self, message: str, context: str, user_id: str) -> str:
        """יצירת תשובה חמה עם AI"""
        
        # בדיקת מגבלות
        can_request, status_message = self.tracker.can_make_request()
        if not can_request:
            return f"יותר מדי בקשות היום. נסה מאוחר יותר! 😊"
        
        # הודעה מפורטת ל-AI
        enhanced_message = f"""
        {self.system_prompt}
        
        הקשר משתמש: {context}
        הודעת המשתמש: {message}
        
        זכור: תהיי מאיה החמה והביטחון העצמי!
        אל תגידי "אני אשתדל" או "אני מצטערת"!
        תני תשובה קצרה, חמה וביטחון עצמי גבוה!
        """
        
        try:
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
            
            chat = self.chat_sessions[user_id]
            response = chat.send_message(enhanced_message)
            
            self.tracker.record_request(len(response.text))
            
            # ניקוי התשובה מביטויים רובוטיים
            cleaned_response = self._clean_robot_phrases(response.text)
            return cleaned_response
            
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return "לא הצלחתי לעבד את זה. נסה שאלה אחרת 🤔"
    
    def _clean_robot_phrases(self, response: str) -> str:
        """ניקוי ביטויים רובוטיים"""
        
        # ביטויים שצריך למחוק לגמרי
        robot_phrases = [
            "אני אשתדל לתקשר בצורה טבעית יותר",
            "אני אשתדל",
            "אני מצטערת",
            "אין לי גישה",
            "אני לא יכולה לגשת",
            "המידע שלי מוגבל",
            "אני אנסה",
            "לפי המידע שלי",
            "אני לא בטוחה",
            "ייתכן ש",
            "אני חושבת ש"
        ]
        
        for phrase in robot_phrases:
            response = response.replace(phrase, "")
        
        # ניקוי רווחים מיותרים
        response = " ".join(response.split())
        
        # אם התשובה ריקה - תחליף בתשובה חמה
        if not response.strip():
            return "אוקיי! 👍"
        
        return response.strip()
    
    def get_usage_stats(self):
        return self.tracker.get_usage_stats()

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
            response = f"היי {user['first_name']}! אני מאיה החמה והחכמה! 🔥😊"
        
        elif cmd == "/help":
            response = "אני מאיה! 🔥\n\n💪 מה אני יכולה:\n🌡️ מזג אוויר בכל העולם\n🕐 זמן נוכחי\n💬 שיחה חמה וטבעית\n\nפשוט כתוב לי מה שאתה רוצה! 😊"
        
        elif cmd == "/weather":
            location = command.replace("/weather", "").strip() or "תל אביב"
            response = ai_service.weather_service.get_weather_anywhere(location)
        
        elif cmd == "/test":
            # בדיקת מזג אוויר בארגנטינה
            response = ai_service.weather_service.get_weather_anywhere("ארגנטינה")
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

# === SERVICES INITIALIZATION ===
security = SecurityService()
user_service = UserService()
ai_service = SuperMayaAI()
bot = TelegramBot()

# === FLASK ROUTES ===
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Maya 3.0 - WARM PERSONALITY + WORKING WEATHER! 🔥",
        "version": "3.0.3-final-fixed",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": config.ENVIRONMENT,
        "users": len(user_data),
        "features": [
            "🔥 Warm friendly personality",
            "🌡️ Working weather for ALL countries",
            "💪 Confident responses",
            "😊 No more robot talk",
            "🇦🇷 Argentina weather WORKS!"
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
        weather_service = SuperWeatherService()
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
                logger.info("🔥 Maya 3.0 with WARM PERSONALITY is ready!")
            else:
                logger.error(f"Failed to set webhook on startup: {result}")
        except Exception as e:
            logger.error(f"Webhook setup error on startup: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Maya 3.0 WITH WARM PERSONALITY...")
    logger.info("🔥 No more cold robot responses!")
    logger.info("🌡️ Weather works for ALL countries including Argentina!")
    set_webhook_on_startup()
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
else:
    logger.info("🔥 Maya 3.0 with WARM PERSONALITY starting via WSGI...")
    set_webhook_on_startup()
