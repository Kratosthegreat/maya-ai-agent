# -*- coding: utf-8 -*-
# Maya Bot - Simple But Smart Version That Actually Works!
import os
import json
import re
import time
import random
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import pytz

app = Flask(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
PORT = int(os.getenv("PORT", 10000))

if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN environment variable")

# Simple but smart response engine
class SmartMaya:
    def __init__(self):
        self.user_names = {}
        self.last_responses = {}
        
        # Smart weather data (fallback if no API)
        self.weather_fallback = {
            "תל אביב": "☀️ תל אביב: 28°C, שמש יפה!",
            "ירושלים": "🌤️ ירושלים: 25°C, נעים ובריא",
            "חיפה": "🌊 חיפה: 26°C, רוח ים נעימה",
            "באר שבע": "🌵 באר שבע: 30°C, חם במדבר",
            "אילת": "🏖️ אילת: 32°C, חום טרופי",
            "נתניה": "🏄 נתניה: 27°C, מושלם לים"
        }
        
        # Time-based greetings
        self.smart_greetings = {
            "morning": [
                "בוקר טוב! ☀️ איך התחלת את היום?",
                "בוקר טוב יקר! ☕ מה התוכניות להיום?", 
                "בוקר טוב! 🌅 קום בחיוך?"
            ],
            "afternoon": [
                "צהריים טובים! 🌤️ איך עובר היום?",
                "שלום! 👋 מקווה שהכל בסדר",
                "צהריים טובים! 😊 מה המצב?"
            ],
            "evening": [
                "ערב טוב! 🌆 איך היה היום?",
                "ערב טוב! 🌙 זמן להירגע קצת",
                "שלום! ערב נעים! 😌"
            ],
            "night": [
                "לילה טוב! 🌙 עדיין ער/ה?",
                "שלום! מאוחר היום 🦉",
                "לילה טוב! מה שומר אותך ער/ה?"
            ]
        }
        
        # Varied responses for different situations
        self.smart_responses = {
            "thanks": [
                "😊 בכיף! תמיד נעים לעזור!",
                "🙏 בבקשה! זה משמח אותי!",
                "❤️ שמחה שיכולתי לעזור!"
            ],
            "weather_no_city": [
                "🤔 איזו עיר מעניינת אותך?",
                "🌍 תגיד לי על איזה מקום אתה רוצה לדעת",
                "🏙️ איזו עיר? יש לי מידע על ערים בישראל"
            ],
            "confused": [
                "🤔 לא בטוחה שהבנתי... תוכל לנסח מחדש?",
                "😅 זה לא ברור לי לגמרי. אולי תסביר קצת יותר?",
                "🧐 אני קצת מבולבלת. תוכל לכתוב בדרך אחרת?"
            ],
            "casual": [
                "😊 איך אוכל לעזור לך היום?",
                "🙂 מה שלומך? במה אוכל לסייע?",
                "😄 שמחה לראות אותך! מה המצב?"
            ]
        }
    
    def get_time_context(self):
        """Get current time context for Israel"""
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        hour = now.hour
        
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon" 
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def get_current_time(self):
        """Get current Israeli time"""
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        hebrew_days = {
            'Monday': 'שני', 'Tuesday': 'שלישי', 'Wednesday': 'רביעי',
            'Thursday': 'חמישי', 'Friday': 'שישי', 'Saturday': 'שבת', 'Sunday': 'ראשון'
        }
        day_name = hebrew_days.get(now.strftime('%A'), now.strftime('%A'))
        return f"📅 היום יום {day_name}, {now.strftime('%d/%m/%Y')}\n🕒 השעה: {now.strftime('%H:%M')}"
    
    def get_weather_real(self, city):
        """Try to get real weather data"""
        if not WEATHER_API_KEY:
            return None
            
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city,
                'appid': WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'he'
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                temp = round(data['main']['temp'])
                desc = data['weather'][0]['description']
                humidity = data['main']['humidity']
                city_name = data['name']
                
                return f"🌤️ מזג האוויר ב{city_name}:\n🌡️ {temp}°C\n☁️ {desc}\n💧 לחות: {humidity}%"
            
        except Exception as e:
            print(f"Weather API error: {e}")
        
        return None
    
    def extract_city(self, message):
        """Extract city name from message"""
        # Hebrew cities
        hebrew_cities = list(self.weather_fallback.keys())
        for city in hebrew_cities:
            if city in message:
                return city
        
        # Check for English city names
        english_words = re.findall(r'[a-zA-Z]+', message)
        if english_words:
            return english_words[0]
        
        return None
    
    def extract_name(self, message):
        """Extract name from introduction"""
        patterns = [
            r'שמי (הוא )?(.+?)(?:\s|$|\.)',
            r'קוראים לי (.+?)(?:\s|$|\.)',
            r'השם שלי (הוא )?(.+?)(?:\s|$|\.)',
            r'אני (.+?)(?:\s|$|\.)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(-1).strip()
                if len(name) > 0 and len(name) < 15:
                    return name
        return None
    
    def get_varied_response(self, response_type, user_id=None):
        """Get varied response to avoid repetition"""
        responses = self.smart_responses.get(response_type, ["😊 כן!"])
        
        if user_id:
            # Track last response for this user
            key = f"{response_type}_{user_id}"
            if key in self.last_responses:
                # Try to get different response
                available = [r for r in responses if r != self.last_responses[key]]
                if available:
                    chosen = random.choice(available)
                else:
                    chosen = random.choice(responses)
            else:
                chosen = random.choice(responses)
            
            self.last_responses[key] = chosen
            return chosen
        
        return random.choice(responses)
    
    def generate_response(self, user_id, message):
        """Generate smart response based on message content"""
        message_lower = message.lower().strip()
        
        # Remove punctuation for better matching
        clean_message = re.sub(r'[^\w\sא-ת]', '', message_lower)
        
        # Check for name introduction
        name = self.extract_name(message)
        if name:
            self.user_names[user_id] = name
            return f"נעים מאוד להכיר אותך, {name}! 😊 איך אוכל לעזור לך?"
        
        # Get user name if we know it
        user_name = self.user_names.get(user_id, "")
        name_suffix = f" {user_name}" if user_name else ""
        
        # Greeting detection
        greeting_words = ['שלום', 'היי', 'הי', 'הייי', 'בוקר טוב', 'ערב טוב', 'לילה טוב']
        if any(word in clean_message for word in greeting_words):
            time_context = self.get_time_context()
            greetings = self.smart_greetings[time_context]
            greeting = random.choice(greetings)
            if name_suffix:
                greeting = greeting.replace("!", f"{name_suffix}!")
            return greeting
        
        # Weather request detection
        weather_keywords = ['מזג אוויר', 'טמפרטורה', 'מעלות', 'חם', 'קר', 'גשם', 'שמש']
        if any(keyword in clean_message for keyword in weather_keywords):
            city = self.extract_city(message)
            
            if city:
                # Try real weather first
                real_weather = self.get_weather_real(city)
                if real_weather:
                    return real_weather
                
                # Fallback to stored data
                if city in self.weather_fallback:
                    return self.weather_fallback[city]
                else:
                    return f"🤔 לא מכיר את {city}. תוכל לנסות עיר אחרת?"
            else:
                return self.get_varied_response("weather_no_city", user_id)
        
        # Time request detection
        time_keywords = ['מה השעה', 'איזה יום', 'תאריך', 'זמן', 'שעה']
        if any(keyword in clean_message for keyword in time_keywords):
            return self.get_current_time()
        
        # Thank you detection
        thank_words = ['תודה', 'מעריך', 'תודה רבה', 'אסיר תודה']
        if any(word in clean_message for word in thank_words):
            return self.get_varied_response("thanks", user_id)
        
        # How are you / status questions
        status_phrases = ['מה שלומך', 'מה נשמע', 'איך אתה', 'איך את', 'מה המצב']
        if any(phrase in clean_message for phrase in status_phrases):
            responses = [
                f"בסדר גמור{name_suffix}! 😊 ואיך אתה?",
                f"הכל טוב{name_suffix}! 👍 מה איתך?",
                f"מעולה{name_suffix}! 😄 איך המצב אצלך?"
            ]
            return random.choice(responses)
        
        # Simple yes/no/ok responses  
        simple_responses = {
            'כן': ['נהדר! 👍', 'מעולה! 😊', 'אחלה! 🙂'],
            'לא': ['אוקיי 👌', 'בסדר! 😊', 'הבנתי 🙂'],
            'אוקיי': ['כן! 👍', 'בסדר! 😊', 'מעולה! 🙂'],
            'בסדר': ['נחמד! 😊', 'יופי! 👍', 'אחלה! 🙂']
        }
        
        for word, responses in simple_responses.items():
            if word in clean_message:
                return random.choice(responses)
        
        # Default responses for unclear messages
        return self.get_varied_response("confused", user_id)

# Initialize Maya
maya = SmartMaya()

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id, text):
        """Send message to Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Send message error: {e}")
            return False
    
    def process_update(self, update):
        """Process incoming update from Telegram"""
        try:
            if "message" not in update:
                return
            
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            user_id = str(message.get("from", {}).get("id", ""))
            
            if not chat_id or not text:
                return
            
            print(f"Processing: {text[:50]}... from user {user_id}")
            
            # Generate smart response
            response = maya.generate_response(user_id, text)
            
            # Send response
            success = self.send_message(chat_id, response)
            if not success:
                # Fallback message
                self.send_message(chat_id, "😅 הייתה בעיה קטנה. תוכל לנסות שוב?")
                
        except Exception as e:
            print(f"Process update error: {e}")
            # Try to send error message
            if "message" in update and "chat" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                self.send_message(chat_id, "😔 מצטער, אירעה שגיאה. אנא נסה שוב.")

# Initialize bot
bot = TelegramBot()

# Flask routes
@app.route("/", methods=["GET"])
def home():
    """Health check"""
    return jsonify({
        "status": "Maya Bot is running! 🚀",
        "version": "Simple & Smart",
        "features": [
            "🧠 Smart Hebrew responses",
            "😊 Personality & greetings", 
            "🌤️ Weather service",
            "💾 User name memory",
            "🎭 Varied responses",
            "⏰ Time awareness"
        ],
        "current_time": maya.get_current_time().replace('\n', ' '),
        "users_remembered": len(maya.user_names)
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Main webhook endpoint"""
    try:
        update = request.get_json()
        if not update:
            return "Bad Request", 400
        
        bot.process_update(update)
        return "OK", 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return "Internal Server Error", 500

@app.route("/test", methods=["GET"])
def test():
    """Test the bot responses"""
    test_messages = [
        "היי מאיה",
        "מה השעה",
        "מה מזג האוויר בתל אביב", 
        "שמי יוסי",
        "תודה רבה",
        "מה שלומך"
    ]
    
    results = {}
    test_user = "test_user_123"
    
    for msg in test_messages:
        response = maya.generate_response(test_user, msg)
        results[msg] = response
    
    return jsonify(results)

@app.route("/stats", methods=["GET"])  
def stats():
    """Bot statistics"""
    return jsonify({
        "users_with_names": len(maya.user_names),
        "last_responses_tracked": len(maya.last_responses),
        "weather_cities_available": len(maya.weather_fallback),
        "status": "All systems operational! 💪"
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Run the app
if __name__ == "__main__":
    print("🚀 Starting Maya Bot - Simple & Smart Version")
    print(f"🌐 Will run on port {PORT}")
    print("✨ Features: Smart responses, weather, time, user memory")
    
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False  # Set to False for production
    )
