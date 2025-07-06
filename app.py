# -*- coding: utf-8 -*-
# Maya Bot - Final Enhanced Version with Research-Based Improvements
import os
import json
import re
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
import pytz
import random
from flask import Flask, request, jsonify, Response
from http import HTTPStatus

# Configuration
class Config:
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        if not self.TELEGRAM_TOKEN:
            raise ValueError("Missing TELEGRAM_TOKEN environment variable")
        
        self.PORT = int(os.getenv("PORT", 10000))
        self.DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
        self.TIMEZONE = pytz.timezone("Asia/Jerusalem")
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
        self.WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# Logging setup
logging.basicConfig(
    level=logging.DEBUG if Config().DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

config = Config()
app = Flask(__name__)

# Hebrew Text Processor - Research-Based
class HebrewTextProcessor:
    def __init__(self):
        self.hebrew_patterns = {
            'letters': r'[\u05D0-\u05EA]',
            'words': r'[\u05D0-\u05EA\u05F0-\u05F4]+',
            'greeting': r'(?:שלום|היי|הי|הייי|בוקר טוב|ערב טוב|צהריים טובים|לילה טוב)',
            'weather_request': r'(?:מזג אוויר|טמפרטורה|מעלות|חם|קר|גשם|שמש|עננים|רוח|לחות)',
            'time_request': r'(?:מה השעה|איזה יום|תאריך|זמן|שעה|כמה השעה)',
            'question_words': r'(?:איך|מה|מתי|איפה|למה|מי|כמה|איזה)',
            'politeness': r'(?:בבקשה|תודה|תודה רבה|סליחה|אני מצטער|מעריך)',
            'name_patterns': [
                r'שמי (הוא )?(.+?)(?:\s|$|\.)',
                r'קוראים לי (.+?)(?:\s|$|\.)',
                r'השם שלי (הוא )?(.+?)(?:\s|$|\.)',
                r'אני (.+?)(?:\s|$|\.)'
            ]
        }
        
        # Israeli cities mapping
        self.city_translations = {
            'תל אביב': 'Tel Aviv',
            'ירושלים': 'Jerusalem', 
            'חיפה': 'Haifa',
            'באר שבע': 'Beer Sheva',
            'אילת': 'Eilat',
            'נתניה': 'Netanya',
            'פתח תקווה': 'Petah Tikva',
            'אשדוד': 'Ashdod',
            'ראשון לציון': 'Rishon LeZion',
            'עפולה': 'Afula',
            'הרצליה': 'Herzliya',
            'כפר סבא': 'Kfar Saba'
        }
    
    def remove_niqqud(self, text: str) -> str:
        """Remove Hebrew diacritics"""
        return re.sub(r'[\u0591-\u05C7]', '', text)
    
    def normalize_text(self, text: str) -> str:
        """Normalize Hebrew text"""
        text = self.remove_niqqud(text)
        text = re.sub(r'\s+', ' ', text.strip())
        return text.lower()
    
    def detect_intent(self, text: str) -> str:
        """Detect intent from Hebrew text"""
        normalized = self.normalize_text(text)
        
        if re.search(self.hebrew_patterns['greeting'], normalized):
            return 'greeting'
        elif re.search(self.hebrew_patterns['weather_request'], normalized):
            return 'weather_request'
        elif re.search(self.hebrew_patterns['time_request'], normalized):
            return 'time_request'
        elif re.search(self.hebrew_patterns['question_words'], normalized):
            return 'question'
        elif re.search(self.hebrew_patterns['politeness'], normalized):
            return 'polite'
        elif any(pattern in normalized for pattern in ['שמי', 'קוראים לי', 'השם שלי']):
            return 'personal_info'
        return 'casual'
    
    def extract_name(self, text: str) -> Optional[str]:
        """Extract name from Hebrew text"""
        for pattern in self.hebrew_patterns['name_patterns']:
            match = re.search(pattern, text)
            if match:
                name = match.group(-1).strip()
                if len(name) > 0 and len(name) < 20:
                    return name
        return None
    
    def extract_city_name(self, text: str) -> Optional[str]:
        """Extract city name from Hebrew text"""
        normalized = self.normalize_text(text)
        
        # Check Hebrew city names
        for hebrew_city, english_city in self.city_translations.items():
            if hebrew_city in normalized:
                return english_city
        
        # Check English words
        english_words = re.findall(r'[a-zA-Z]+', text)
        return english_words[0] if english_words else None

# Weather Service with Error Handling
class WeatherService:
    def __init__(self):
        self.api_key = config.WEATHER_API_KEY
        self.base_url = config.WEATHER_API_URL
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_weather(self, city: str) -> Dict[str, Any]:
        """Get weather with comprehensive error handling"""
        cache_key = f"weather:{city}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        if not self.api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'he'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                formatted_data = self._format_weather_data(data)
                self.cache[cache_key] = (formatted_data, time.time())
                return formatted_data
            
            elif response.status_code == 404:
                return {"success": False, "error": "city_not_found"}
            elif response.status_code == 401:
                logger.error("Invalid API key")
                return {"success": False, "error": "api_key_invalid"}
            else:
                logger.error(f"API error: {response.status_code}")
                return {"success": False, "error": "api_error"}
        
        except requests.exceptions.Timeout:
            logger.error("API timeout")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(f"Unexpected weather error: {e}")
            return {"success": False, "error": "unexpected_error"}
    
    def _format_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format weather data"""
        try:
            return {
                "success": True,
                "city": data["name"],
                "temperature": round(data["main"]["temp"]),
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "feels_like": round(data["main"]["feels_like"]),
                "wind_speed": data.get("wind", {}).get("speed", 0)
            }
        except KeyError as e:
            logger.error(f"Weather data format error: {e}")
            return {"success": False, "error": "data_format_error"}

# Bot Personality Engine - Research-Based Improvements
class BotPersonality:
    def __init__(self):
        self.conversation_context = {}
        self.user_preferences = {}
        self.used_responses = {}
        
        # Time-based greetings
        self.time_greetings = {
            "morning": [
                "בוקר טוב! ☀️ איך השינה? מה התוכניות להיום?",
                "בוקר טוב! 🌅 קום עם חיוך? איך אוכל לעזור?",
                "בוקר טוב יקר! ☕ מקווה שהתחלת את היום טוב!"
            ],
            "afternoon": [
                "צהריים טובים! 🌤️ איך עובר היום?",
                "שלום! 👋 איך החלק הראשון של היום?",
                "צהריים טובים! 🍽️ מקווה שאכלת משהו טוב!"
            ],
            "evening": [
                "ערב טוב! 🌆 איך היה היום?",
                "ערב טוב! 🌙 מתחיל להירגע?",
                "שלום! ערב נעים! איך אפשר לעזור?"
            ],
            "night": [
                "לילה טוב! 🌙 עדיין ער/ה?",
                "שלום! מאוחר היום, אבל אני כאן! 🦉",
                "לילה טוב! מה שומר אותך ער/ה?"
            ]
        }
        
        # Varied responses to prevent repetition
        self.response_variations = {
            'weather_success': [
                "🌤️ הנה מזג האוויר ב{city}:\n\n🌡️ טמפרטורה: {temperature}°C\n🤔 מרגיש כמו: {feels_like}°C\n☁️ מצב: {description}\n💧 לחות: {humidity}%",
                "☀️ מידע מזג אוויר עבור {city}:\n\n🌡️ כרגע: {temperature}°C (מרגיש {feels_like}°C)\n🌤️ תיאור: {description}\n💧 לחות באוויר: {humidity}%",
                "🌈 דו\"ח מזג אוויר - {city}:\n\n🌡️ טמפרטורה נוכחית: {temperature}°C\n😊 תחושה: {feels_like}°C\n☁️ מה קורה בשמיים: {description}\n💧 לחות: {humidity}%"
            ],
            'weather_error': [
                "🤔 לא הצלחתי למצוא את העיר הזו... אולי תנסה לכתוב בדרך אחרת?",
                "😅 העיר לא נמצאה במאגר שלי. אולי יש שגיאת כתיב?",
                "🔍 לא מכיר את המקום הזה. תוכל לנסות שם אחר או לבדוק את הכתיב?"
            ],
            'no_api': [
                "😔 מצטער, השירות לא זמין כרגע. נסה שוב מאוחר יותר!",
                "🚧 יש בעיה זמנית עם שירות מזג האוויר. תחזור בעוד קצת?",
                "⚠️ לא יכול לגשת לנתוני מזג אוויר עכשיו. אנא נסה מאוחר יותר."
            ],
            'unknown': [
                "🤔 לא בטוח שהבנתי... תוכל לנסח מחדש?",
                "😅 זה לא ברור לי לגמרי. אולי תסביר קצת יותר?",
                "🧐 אני קצת מבולבל. תוכל לכתוב בדרך אחרת?"
            ],
            'thanks': [
                "😊 בכיף! תמיד נעים לעזור!",
                "🙏 בבקשה! זה הכי משמח אותי!",
                "❤️ שמח שיכולתי לעזור! יש עוד משהו?"
            ]
        }
    
    def get_time_context(self) -> str:
        """Get current time context"""
        hour = datetime.now(config.TIMEZONE).hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def get_time_based_greeting(self, user_id: int = None) -> str:
        """Get time-appropriate greeting"""
        time_context = self.get_time_context()
        greetings = self.time_greetings[time_context]
        
        # Avoid repetition per user
        if user_id:
            key = f"greeting_{user_id}"
            if key in self.used_responses:
                available = [g for g in greetings if g not in self.used_responses[key]]
                if not available:
                    self.used_responses[key] = []
                    available = greetings
            else:
                available = greetings
                self.used_responses[key] = []
            
            chosen = random.choice(available)
            self.used_responses[key].append(chosen)
            return chosen
        
        return random.choice(greetings)
    
    def get_varied_response(self, response_type: str, user_id: int = None, **kwargs) -> str:
        """Get varied response to prevent repetition"""
        if response_type not in self.response_variations:
            return "אני כאן לעזור! איך אוכל לסייע?"
        
        variations = self.response_variations[response_type]
        
        # Avoid repetition per user
        if user_id:
            key = f"{response_type}_{user_id}"
            if key in self.used_responses:
                available = [v for v in variations if v not in self.used_responses[key]]
                if not available:
                    self.used_responses[key] = []
                    available = variations
            else:
                available = variations
                self.used_responses[key] = []
            
            chosen = random.choice(available)
            self.used_responses[key].append(chosen)
        else:
            chosen = random.choice(variations)
        
        return chosen.format(**kwargs)
    
    def remember_user_info(self, user_id: int, info_type: str, value: str):
        """Remember user information"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        self.user_preferences[user_id][info_type] = value
    
    def get_user_name(self, user_id: int) -> Optional[str]:
        """Get remembered user name"""
        return self.user_preferences.get(user_id, {}).get('name')

# Enhanced Response Engine
class EnhancedResponseEngine:
    def __init__(self):
        self.text_processor = HebrewTextProcessor()
        self.weather_service = WeatherService()
        self.personality = BotPersonality()
    
    def process_message(self, user_id: int, message: str) -> str:
        """Process message and generate intelligent response"""
        try:
            # Detect intent
            intent = self.text_processor.detect_intent(message)
            logger.info(f"Detected intent: {intent} for user {user_id}")
            
            # Handle different intents
            if intent == 'greeting':
                return self._handle_greeting(user_id)
            
            elif intent == 'weather_request':
                return self._handle_weather_request(user_id, message)
            
            elif intent == 'time_request':
                return self._handle_time_request(user_id)
            
            elif intent == 'personal_info':
                return self._handle_personal_info(user_id, message)
            
            elif intent == 'polite':
                return self._handle_politeness(user_id, message)
            
            else:
                return self._handle_casual_chat(user_id)
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "😅 מצטער, הייתה לי בעיה קטנה. אוכל לנסות שוב?"
    
    def _handle_greeting(self, user_id: int) -> str:
        """Handle greeting messages"""
        user_name = self.personality.get_user_name(user_id)
        greeting = self.personality.get_time_based_greeting(user_id)
        
        if user_name:
            greeting = greeting.replace("!", f" {user_name}!")
        
        return greeting
    
    def _handle_weather_request(self, user_id: int, message: str) -> str:
        """Handle weather requests"""
        city = self.text_processor.extract_city_name(message)
        
        if not city:
            return "🤔 איזו עיר מעניינת אותך? תוכל לכתוב את השם?"
        
        weather_data = self.weather_service.get_weather(city)
        
        if weather_data['success']:
            return self.personality.get_varied_response(
                'weather_success', user_id, **weather_data
            )
        else:
            if weather_data['error'] == 'city_not_found':
                return self.personality.get_varied_response('weather_error', user_id)
            else:
                return self.personality.get_varied_response('no_api', user_id)
    
    def _handle_time_request(self, user_id: int) -> str:
        """Handle time/date requests"""
        now = datetime.now(config.TIMEZONE)
        hebrew_days = {
            'Monday': 'שני', 'Tuesday': 'שלישי', 'Wednesday': 'רביעי',
            'Thursday': 'חמישי', 'Friday': 'שישי', 'Saturday': 'שבת', 'Sunday': 'ראשון'
        }
        day_name = hebrew_days.get(now.strftime('%A'), now.strftime('%A'))
        
        return (f"📅 היום יום {day_name}, {now.strftime('%d/%m/%Y')}\n"
               f"🕒 השעה בישראל: {now.strftime('%H:%M')}")
    
    def _handle_personal_info(self, user_id: int, message: str) -> str:
        """Handle personal information sharing"""
        name = self.text_processor.extract_name(message)
        
        if name:
            self.personality.remember_user_info(user_id, 'name', name)
            responses = [
                f"נעים מאוד להכיר אותך, {name}! 😊 איך אוכל לעזור לך?",
                f"שמח להכיר, {name}! 👋 מה שלומך היום?",
                f"היי {name}! 🙂 נחמד שאתה כאן. במה אוכל לסייע?"
            ]
            return random.choice(responses)
        
        return "תודה שאתה חולק איתי! 😊 זה עוזר לי להכיר אותך יותר טוב."
    
    def _handle_politeness(self, user_id: int, message: str) -> str:
        """Handle polite expressions"""
        if any(word in message for word in ['תודה', 'מעריך']):
            return self.personality.get_varied_response('thanks', user_id)
        
        return "😊 בכיף! אני כאן בשבילך."
    
    def _handle_casual_chat(self, user_id: int) -> str:
        """Handle casual conversation"""
        return self.personality.get_varied_response('unknown', user_id)

# Main Bot Class
class MayaBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.response_engine = EnhancedResponseEngine()
    
    def send_message(self, chat_id: int, text: str) -> bool:
        """Send message with error handling"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def process_update(self, update: Dict[str, Any]):
        """Process incoming update"""
        try:
            if "message" not in update:
                return
            
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            user_id = message.get("from", {}).get("id")
            
            if not chat_id or not text or not user_id:
                return
            
            logger.info(f"Processing message from user {user_id}: {text[:50]}...")
            
            # Generate response
            response = self.response_engine.process_message(user_id, text)
            
            # Send response
            success = self.send_message(chat_id, response)
            if not success:
                # Fallback message
                self.send_message(chat_id, "😅 הייתה בעיה קטנה. תוכל לנסות שוב?")
        
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            if "message" in update and "chat" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                self.send_message(chat_id, "😔 מצטער, אירעה שגיאה. אנא נסה שוב.")

# Flask Routes
bot = MayaBot()

@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "Maya Bot is running! 🤖",
        "version": "7.0 - Enhanced",
        "features": [
            "🧠 Smart Hebrew NLP",
            "😊 Personality Engine", 
            "🌤️ Weather Service",
            "💾 User Memory",
            "🎭 Varied Responses",
            "⏰ Time-Aware Greetings"
        ],
        "timestamp": datetime.now().isoformat()
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for Telegram"""
    try:
        update = request.get_json()
        if not update:
            logger.warning("Empty webhook update received")
            return Response(status=HTTPStatus.BAD_REQUEST)
        
        bot.process_update(update)
        return Response(status=HTTPStatus.OK)
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route("/test", methods=["GET"])
def test_responses():
    """Test endpoint for response variations"""
    test_messages = [
        "היי",
        "מה השעה", 
        "מה מזג האוויר בתל אביב",
        "שמי דני",
        "תודה רבה",
        "איך אתה"
    ]
    
    results = {}
    test_user_id = 999999
    
    for message in test_messages:
        response = bot.response_engine.process_message(test_user_id, message)
        results[message] = response
    
    return jsonify(results)

@app.route("/stats", methods=["GET"])
def stats():
    """Bot statistics"""
    return jsonify({
        "active_users": len(bot.response_engine.personality.user_preferences),
        "cached_weather": len(bot.response_engine.weather_service.cache),
        "response_variations": len(bot.response_engine.personality.response_variations),
        "uptime": "Running smoothly! 💪"
    })

# Error handler
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

# Run the application
if __name__ == "__main__":
    logger.info("Starting Maya Bot - Enhanced Version 7.0")
    logger.info("Features: Smart NLP, Personality Engine, Weather Service")
    
    app.run(
        host="0.0.0.0", 
        port=config.PORT, 
        debug=config.DEBUG
    )
