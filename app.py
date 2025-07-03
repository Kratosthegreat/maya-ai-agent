"""
Maya Secretary Bot - Fixed for google-generativeai 0.3.2
Compatible with Python 3.13 - Uses JSON for data storage
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import pytz
from typing import Dict, Any, Optional
import time

# Third-party imports
import google.generativeai as genai
from config import config

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === FLASK APP SETUP ===
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# === DATA STORAGE (JSON) ===
DATA_FILE = "maya_data.json"
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
    except Exception as e:
        logger.error(f"Error saving data: {e}")

# Load data on startup
load_data()

# === SECURITY & RATE LIMITING ===
class SecurityService:
    """Simple security service"""
    
    def __init__(self):
        self.rate_limits = {}
    
    def is_rate_limited(self, user_id: str) -> bool:
        """Check if user is rate limited"""
        now = time.time()
        user_requests = self.rate_limits.get(user_id, [])
        
        # Clean old requests
        recent_requests = [ts for ts in user_requests if now - ts < 60]
        self.rate_limits[user_id] = recent_requests
        
        if len(recent_requests) >= config.MAX_REQUESTS_PER_MINUTE:
            return True
        
        self.rate_limits[user_id].append(now)
        return False

security = SecurityService()

# === AI SERVICE ===
class AIService:
    """AI service for generating responses - Fixed for google-generativeai 0.3.2"""
    
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        # In older versions, no system_instruction parameter
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        self.chat_sessions = {}
        self.system_instruction = self._get_system_instruction()
    
    def _get_system_instruction(self) -> str:
        """Get system instruction text"""
        return """
        את מאיה, מזכירה אישית חכמה ונעימה. תמיד דברי על עצמך בלשון נקבה.
        
        התפקיד שלך:
        1. לעזור למשתמשים בניהול זמן ומשימות
        2. לזכור מידע חשוב על המשתמשים
        3. לספק מידע מדויק ועדכני
        4. להיות חברותית ומקצועית
        
        תמיד התייחסי למשתמש בכבוד וזכרי פרטים חשובים משיחות קודמות.
        """
    
    def generate_response(self, user_id: str, message: str, context: str = "") -> str:
        """Generate AI response"""
        try:
            # Create enhanced message with system instruction included
            enhanced_message = f"""
            {self.system_instruction}
            
            הודעת המשתמש: {message}
            הקשר: {context}
            השעה: {datetime.now().strftime('%H:%M')}
            
            עני כמאיה, המזכירה החכמה בלשון נקבה.
            """
            
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
            
            chat = self.chat_sessions[user_id]
            response = chat.send_message(enhanced_message)
            return response.text
        except Exception as e:
            logger.error(f"AI error: {e}")
            return "מצטערת, קרתה לי שגיאה קטנה. אפשר לנסות שוב? 😊"

ai_service = AIService()

# === USER SERVICE ===
class UserService:
    """User management service"""
    
    def get_or_create_user(self, telegram_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get or create user"""
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
        """Update user activity"""
        if user_id in user_data:
            user_data[user_id]['last_activity'] = datetime.now().isoformat()
            user_data[user_id]['total_messages'] += 1
            save_data()
    
    def get_user_context(self, user_id: str) -> str:
        """Get user context for AI"""
        user = user_data.get(user_id, {})
        user_memories = memories.get(user_id, [])
        
        context = f"""
        משתמש: {user.get('first_name', 'חבר/ה')}
        הודעות: {user.get('total_messages', 0)}
        זיכרונות: {', '.join(user_memories[-5:]) if user_memories else 'אין'}
        """
        
        return context
    
    def add_memory(self, user_id: str, content: str):
        """Add user memory"""
        if user_id not in memories:
            memories[user_id] = []
        
        memories[user_id].append(content)
        
        # Keep only last 10 memories
        if len(memories[user_id]) > 10:
            memories[user_id] = memories[user_id][-10:]
        
        save_data()

user_service = UserService()

# === WEATHER SERVICE ===
class WeatherService:
    """Weather service"""
    
    CITIES = {
        "תל אביב": (32.0853, 34.7818),
        "ירושלים": (31.7683, 35.2137),
        "חיפה": (32.7940, 34.9896),
        "באר שבע": (31.2518, 34.7915),
        "עפולה": (32.6098, 35.2897),
        "בני ברק": (32.0879, 34.8336)
    }
    
    def extract_city(self, text: str) -> str:
        """Extract city from text"""
        for city in self.CITIES:
            if city in text:
                return city
        return "תל אביב"
    
    def get_weather(self, city: str = "תל אביב") -> str:
        """Get weather for city"""
        try:
            lat, lon = self.CITIES.get(city, self.CITIES["תל אביב"])
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            
            response = requests.get(url, timeout=5)
            data = response.json()
            
            current = data["current_weather"]
            temp = current["temperature"]
            windspeed = current["windspeed"]
            
            return f"🌤️ מזג האוויר ב{city}:\n🌡️ {temp}°C\n💨 רוח: {windspeed} קמ\"ש"
        except Exception as e:
            logger.error(f"Weather error: {e}")
            return f"❗ לא הצלחתי לקבל מזג אוויר עבור {city}"

weather_service = WeatherService()

# === TELEGRAM BOT LOGIC ===
class TelegramBot:
    """Telegram bot handler"""
    
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = None):
        """Send message to Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text[:4096],  # Telegram limit
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return {"ok": False, "error": str(e)}
    
    def process_update(self, update: Dict[str, Any]):
        """Process incoming update"""
        try:
            if "message" not in update:
                return
            
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_data_tg = message.get("from", {})
            text = message.get("text", "")
            
            # Rate limiting
            if security.is_rate_limited(str(user_data_tg.get("id", 0))):
                self.send_message(chat_id, "⚠️ יותר מדי בקשות. המתן דקה ונסה שוב.")
                return
            
            # Get or create user
            user = user_service.get_or_create_user(user_data_tg)
            user_service.update_user_activity(user['telegram_id'])
            
            # Handle commands
            if text.startswith('/'):
                self._handle_command(chat_id, text, user)
            else:
                self._handle_message(chat_id, text, user)
                
        except Exception as e:
            logger.error(f"Process update error: {e}")
    
    def _handle_command(self, chat_id: int, command: str, user: Dict[str, Any]):
        """Handle bot commands"""
        cmd = command.split()[0].lower()
        
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
/forget - מחק זיכרון

פשוט כתוב לי מה שאתה צריך! 💪
            """
        
        elif cmd == "/memory":
            context = user_service.get_user_context(user['telegram_id'])
            response = f"🧠 הנה מה שאני זוכרת עליך:\n\n{context}"
        
        elif cmd == "/weather":
            city = weather_service.extract_city(command)
            response = weather_service.get_weather(city)
        
        elif cmd == "/stats":
            total_users = len(user_data)
            total_conversations = sum(len(conversations.get(uid, [])) for uid in conversations)
            response = f"📊 סטטיסטיקות:\n👥 משתמשים: {total_users}\n💬 שיחות: {total_conversations}\n🤖 אני פעילה!"
        
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
        
        self.send_message(chat_id, response)
    
    def _handle_message(self, chat_id: int, text: str, user: Dict[str, Any]):
        """Handle regular messages"""
        user_id = user['telegram_id']
        
        # Weather check
        if any(word in text.lower() for word in ["מזג אוויר", "טמפרטורה", "חם", "קר"]):
            city = weather_service.extract_city(text)
            response = weather_service.get_weather(city)
        
        # Time check
        elif "שעה" in text.lower():
            israel_tz = pytz.timezone("Asia/Jerusalem")
            now = datetime.now(israel_tz)
            response = f"🕐 השעה בישראל: {now.strftime('%H:%M')}\n📅 {now.strftime('%A, %d %B %Y')}"
        
        # Save important info
        elif any(phrase in text.lower() for phrase in ["קוראים לי", "אני עובד", "אני גר"]):
            user_service.add_memory(user_id, text)
            context = user_service.get_user_context(user_id)
            response = ai_service.generate_response(user_id, text, context)
        
        # Regular AI response
        else:
            context = user_service.get_user_context(user_id)
            response = ai_service.generate_response(user_id, text, context)
        
        # Log conversation
        if user_id not in conversations:
            conversations[user_id] = []
        conversations[user_id].append({
            'message': text,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 20 conversations
        if len(conversations[user_id]) > 20:
            conversations[user_id] = conversations[user_id][-20:]
        
        save_data()
        self.send_message(chat_id, response)

bot = TelegramBot()

# === FLASK ROUTES ===
@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Maya Secretary Bot",
        "version": "2.0.0-compatible",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": config.ENVIRONMENT,
        "users": len(user_data),
        "storage": "JSON",
        "ai_model": config.GEMINI_MODEL
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for Telegram"""
    try:
        update = request.get_json()
        if update:
            bot.process_update(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route("/stats", methods=["GET"])
def api_stats():
    """API stats endpoint"""
    try:
        stats = {
            "total_users": len(user_data),
            "active_users": sum(1 for u in user_data.values() if u.get('is_active', True)),
            "total_conversations": sum(len(conversations.get(uid, [])) for uid in conversations),
            "total_memories": sum(len(memories.get(uid, [])) for uid in memories),
            "bot_status": "active",
            "storage_type": "JSON",
            "ai_model": config.GEMINI_MODEL
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": "Stats unavailable"}), 500

@app.route("/set_webhook", methods=["POST"])
def set_webhook():
    """Set webhook endpoint"""
    try:
        webhook_url = config.WEBHOOK_URL
        if not webhook_url:
            return jsonify({"error": "WEBHOOK_URL not configured"}), 400
        
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
        data = {"url": webhook_url}
        
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

# === ERROR HANDLERS ===
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# === STARTUP ===
def set_webhook_on_startup():
    """Set webhook on startup"""
    if config.ENVIRONMENT == "production" and config.WEBHOOK_URL:
        try:
            url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
            data = {"url": config.WEBHOOK_URL}
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"✅ Webhook set: {config.WEBHOOK_URL}")
            else:
                logger.error(f"❌ Failed to set webhook: {result}")
        except Exception as e:
            logger.error(f"❌ Webhook setup error: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Maya Secretary Bot (Compatible Version)...")
    logger.info(f"🌍 Environment: {config.ENVIRONMENT}")
    logger.info(f"💾 Storage: JSON files")
    logger.info(f"🤖 AI Model: {config.GEMINI_MODEL}")
    logger.info(f"📦 Google GenAI: Compatible with 0.3.2")
    
    # Set webhook for production
    set_webhook_on_startup()
    
    # Run Flask app
    app.run(
        host="0.0.0.0",
        port=config.PORT,
        debug=config.DEBUG
    )
else:
    # For production servers (gunicorn)
    set_webhook_on_startup()
