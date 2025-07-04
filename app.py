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
                logger.info(f"✅ Loaded data for {len(user_data)} users")
        else:
            logger.info("📁 No existing data file, starting fresh")
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")
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
        logger.debug("💾 Data saved successfully")
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

# Load data on startup
load_data()

# === GEMINI API TRACKER (חדש!) ===
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
                logger.debug(f"📊 Loaded usage: {self.usage_data.get('daily_requests', 0)} requests today")
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
            logger.error(f"❌ Error saving usage: {e}")
    
    def can_make_request(self):
        # Reset if new day
        today = str(datetime.now().date())
        if self.usage_data['last_reset'] != today:
            self.usage_data['daily_requests'] = 0
            self.usage_data['last_reset'] = today
            self.usage_data['minute_requests'] = []
        
        # Clean old minute requests
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        self.usage_data['minute_requests'] = [
            req_time for req_time in self.usage_data['minute_requests']
            if datetime.fromisoformat(req_time) > minute_ago
        ]
        
        # Check limits
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
        logger.info(f"📊 Recorded: {self.usage_data['daily_requests']}/{self.daily_limit}, Tokens: {tokens_used}")
    
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
            logger.warning(f"🚫 Rate limit exceeded for user {user_id}")
            return True
        
        self.rate_limits[user_id].append(now)
        return False

security = SecurityService()

# === AI SERVICE ===
class AIService:
    """AI service for generating responses"""
    
    def __init__(self):
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            self.chat_sessions = {}
            self.system_instruction = self._get_system_instruction()
            self.tracker = GeminiTracker()  # חדש!
            logger.info(f"✅ AI Service initialized with model: {config.GEMINI_MODEL}")
            
            # Log initial usage
            stats = self.tracker.get_usage_stats()
            logger.info(f"📊 Usage today: {stats['daily_requests']}/{stats['daily_limit']} ({stats['percentage_used_today']}%)")
            
        except Exception as e:
            logger.error(f"❌ AI Service initialization failed: {e}")
            raise
    
    def _get_system_instruction(self) -> str:
        """Get system instruction text"""
        return """
        את מאיה, מזכירה אישית ישראלית. כללים חשובים:
    
        1. אל תברכי "שלום" בכל הודעה - רק בהודעה הראשונה
        2. תני תשובות קצרות ומדויקות (1-2 משפטים)
        3. אם שאלו אותך על מקום ספציפי - תני מידע על המקום הזה בדיוק
        4. זכרי את ההקשר של השיחה הקודמת
        5. דברי דוגרי וישר, בלי פרפרות
        6. אם אתה לא יודעת משהו - תגידי שאתה לא יודעת
    
        עני רק על השאלה שנשאלה, בקצרה ובעניין.
        """
    
    def generate_response(self, user_id: str, message: str, context: str = "") -> str:
        """Generate AI response"""
    
            # בדיקת מגבלות - חדש!
            can_request, status_message = self.tracker.can_make_request()
            if not can_request:
                logger.warning(f"🚫 Limit reached: {status_message}")
                return f"מצטערת, {status_message}\n\nנסה שוב מאוחר יותר! 😊"
            
            logger.debug(f"🤖 Generating response for user {user_id}: {message[:50]}...")
            
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
                logger.debug(f"🆕 Created new chat session for user {user_id}")
            
            chat = self.chat_sessions[user_id]
            response = chat.send_message(enhanced_message)
            
            # רישום הבקשה - חדש!
            tokens_used = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_used = getattr(response.usage_metadata, 'total_token_count', 0)
            self.tracker.record_request(tokens_used)
            
            logger.debug(f"✅ AI response generated: {response.text[:100]}...")
            return response.text
            
        except Exception as e:
            logger.error(f"❌ AI generation error for user {user_id}: {e}")
            if "429" in str(e) or "quota" in str(e).lower():
                return "מצטערת, הגעתי למגבלת השימוש. אני אחזור מחר! 😊"
            return "מצטערת, קרתה לי שגיאה קטנה. אפשר לנסות שוב? 😊"
    
    def get_usage_stats(self):  # חדש!
        """Get Gemini API usage statistics"""
        return self.tracker.get_usage_stats()

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
            logger.info(f"👤 Created new user: {user_id} ({telegram_data.get('first_name', 'Unknown')})")
        
        return user_data[user_id]
    
    def update_user_activity(self, user_id: str):
        """Update user activity"""
        if user_id in user_data:
            user_data[user_id]['last_activity'] = datetime.now().isoformat()
            user_data[user_id]['total_messages'] += 1
            save_data()
            logger.debug(f"📈 Updated activity for user {user_id}")
    
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
        logger.debug(f"🧠 Added memory for user {user_id}: {content[:50]}...")

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
            
            result = f"🌤️ מזג האוויר ב{city}:\n🌡️ {temp}°C\n💨 רוח: {windspeed} קמ\"ש"
            logger.debug(f"🌤️ Weather fetched for {city}: {temp}°C")
            return result
            
        except Exception as e:
            logger.error(f"❌ Weather error for {city}: {e}")
            return f"❗ לא הצלחתי לקבל מזג אוויר עבור {city}"

weather_service = WeatherService()

# === TELEGRAM BOT LOGIC ===
class TelegramBot:
    """Telegram bot handler"""
    
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        logger.info(f"🤖 Telegram bot initialized with token: {self.token[:10]}...")
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = None):
        """Send message to Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text[:4096],  # Telegram limit
            }
            
            logger.debug(f"📤 Sending message to chat {chat_id}: {text[:50]}...")
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.debug(f"✅ Message sent successfully to chat {chat_id}")
            else:
                logger.error(f"❌ Failed to send message: {result}")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Send message error: {e}")
            return {"ok": False, "error": str(e)}
    
    def process_update(self, update: Dict[str, Any]):
        """Process incoming update"""
        try:
            logger.debug(f"📥 Processing update: {json.dumps(update, indent=2)}")
            
            if "message" not in update:
                logger.debug("⚠️ No message in update, skipping")
                return
            
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_data_tg = message.get("from", {})
            text = message.get("text", "")
            
            logger.info(f"📨 Received message from {user_data_tg.get('first_name', 'Unknown')} (ID: {user_data_tg.get('id')}): {text}")
            
            # Rate limiting
            if security.is_rate_limited(str(user_data_tg.get("id", 0))):
                self.send_message(chat_id, "⚠️ יותר מדי בקשות. המתן דקה ונסה שוב.")
                return
            
            # Get or create user
            user = user_service.get_or_create_user(user_data_tg)
            user_service.update_user_activity(user['telegram_id'])
            
            # Handle commands
            if text.startswith('/'):
                logger.debug(f"🎯 Processing command: {text}")
                self._handle_command(chat_id, text, user)
            else:
                logger.debug(f"💬 Processing regular message: {text}")
                self._handle_message(chat_id, text, user)
                
        except Exception as e:
            logger.error(f"❌ Process update error: {e}")
            logger.error(f"Update data: {json.dumps(update, indent=2)}")
    
    def _handle_command(self, chat_id: int, command: str, user: Dict[str, Any]):
        """Handle bot commands"""
        cmd = command.split()[0].lower()
        logger.debug(f"🎯 Handling command: {cmd}")
        
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
            city = weather_service.extract_city(command)
            response = weather_service.get_weather(city)
        
        elif cmd == "/stats":
            total_users = len(user_data)
            total_conversations = sum(len(conversations.get(uid, [])) for uid in conversations)
            response = f"📊 סטטיסטיקות:\n👥 משתמשים: {total_users}\n💬 שיחות: {total_conversations}\n🤖 אני פעילה!"
        
        elif cmd == "/usage":  # חדש!
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
        
        logger.debug(f"📝 Command response: {response[:50]}...")
        self.send_message(chat_id, response)
    
    def _handle_message(self, chat_id: int, text: str, user: Dict[str, Any]):
        """Handle regular messages"""
        user_id = user['telegram_id']
        
        # Weather check
        if any(word in text.lower() for word in ["מזג אוויר", "טמפרטורה", "חם", "קר"]):
    logger.debug("🌤️ Weather query detected")
    
    # בדיקה אם מדובר על מקום שלא בישראל
    if "ארגנטינה" in text or "argentina" in text.lower():
        response = "מצטערת, אני יכולה לתת מזג אוויר רק לערים בישראל 🇮🇱\nאיזה עיר בישראל מעניינת אותך?"
    else:
        city = weather_service.extract_city(text)
        response = weather_service.get_weather(city)
        
        # Time check
        elif "שעה" in text.lower():
            logger.debug("🕐 Time query detected")
            israel_tz = pytz.timezone("Asia/Jerusalem")
            now = datetime.now(israel_tz)
            response = f"🕐 השעה בישראל: {now.strftime('%H:%M')}\n📅 {now.strftime('%A, %d %B %Y')}"
        
        # Save important info
        elif any(phrase in text.lower() for phrase in ["קוראים לי", "אני עובד", "אני גר"]):
            logger.debug("🧠 Important info detected, saving to memory")
            user_service.add_memory(user_id, text)
            context = user_service.get_user_context(user_id)
            response = ai_service.generate_response(user_id, text, context)
        
        # Regular AI response
        else:
            logger.debug("🤖 Generating AI response")
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
        
        logger.debug(f"📝 Message response: {response[:50]}...")
        self.send_message(chat_id, response)

bot = TelegramBot()

# === FLASK ROUTES ===
@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        usage_stats = ai_service.get_usage_stats()  # חדש!
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
            "gemini_usage": {  # חדש!
                "daily_requests": usage_stats['daily_requests'],
                "daily_limit": usage_stats['daily_limit'],
                "percentage_used": usage_stats['percentage_used_today']
            }
        })
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for Telegram"""
    try:
        logger.info("🔔 Webhook called")
        update = request.get_json()
        
        if not update:
            logger.warning("⚠️ Empty webhook request")
            return "No data", 400
        
        logger.debug(f"📥 Webhook data: {json.dumps(update, indent=2)}")
        bot.process_update(update)
        
        logger.info("✅ Webhook processed successfully")
        return "OK", 200
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return "Error", 500

@app.route("/stats", methods=["GET"])
def api_stats():
    """API stats endpoint"""
    try:
        usage_stats = ai_service.get_usage_stats()  # חדש!
        stats = {
            "total_users": len(user_data),
            "active_users": sum(1 for u in user_data.values() if u.get('is_active', True)),
            "total_conversations": sum(len(conversations.get(uid, [])) for uid in conversations),
            "total_memories": sum(len(memories.get(uid, [])) for uid in memories),
            "bot_status": "active",
            "storage_type": "JSON",
            "ai_model": config.GEMINI_MODEL,
            "webhook_url": config.WEBHOOK_URL,
            "gemini_usage": usage_stats  # חדש!
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return jsonify({"error": "Stats unavailable"}), 500

@app.route("/usage", methods=["GET"])  # חדש!
def api_usage():
    """Gemini API usage endpoint"""
    try:
        usage_stats = ai_service.get_usage_stats()
        return jsonify(usage_stats)
    except Exception as e:
        logger.error(f"❌ Usage stats error: {e}")
        return jsonify({"error": "Usage stats unavailable"}), 500

@app.route("/set_webhook", methods=["POST"])
def set_webhook():
    """Set webhook endpoint"""
    try:
        webhook_url = config.WEBHOOK_URL
        if not webhook_url:
            return jsonify({"error": "WEBHOOK_URL not configured"}), 400
        
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
        data = {"url": webhook_url}
        
        logger.info(f"🔗 Setting webhook to: {webhook_url}")
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            logger.info(f"✅ Webhook set successfully: {webhook_url}")
            return jsonify({"success": True, "webhook_url": webhook_url})
        else:
            logger.error(f"❌ Failed to set webhook: {result}")
            return jsonify({"error": "Failed to set webhook"}), 500
    
    except Exception as e:
        logger.error(f"❌ Set webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/debug", methods=["GET"])
def debug_info():
    """Debug information endpoint"""
    try:
        usage_stats = ai_service.get_usage_stats()  # חדש!
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
        logger.error(f"❌ Debug info error: {e}")
        return jsonify({"error": str(e)}), 500

# === ERROR HANDLERS ===
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"⚠️ 404 error: {request.url}")
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# === STARTUP ===
def set_webhook_on_startup():
    """Set webhook on startup"""
    if config.ENVIRONMENT == "production" and config.WEBHOOK_URL:
        try:
            url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
            data = {"url": config.WEBHOOK_URL}
            
            logger.info(f"🔗 Setting webhook on startup: {config.WEBHOOK_URL}")
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"✅ Webhook set on startup: {config.WEBHOOK_URL}")
            else:
                logger.error(f"❌ Failed to set webhook on startup: {result}")
        except Exception as e:
            logger.error(f"❌ Webhook setup error on startup: {e}")
    else:
        logger.info("⚠️ Webhook not set - missing WEBHOOK_URL or not in production")

if __name__ == "__main__":
    logger.info("🚀 Starting Maya Secretary Bot...")
    logger.info(f"🌍 Environment: {config.ENVIRONMENT}")
    logger.info(f"🔧 Debug mode: {config.DEBUG}")
    logger.info(f"💾 Storage: JSON files")
    logger.info(f"🤖 AI Model: {config.GEMINI_MODEL}")
    
    try:
        usage_stats = ai_service.get_usage_stats()
        logger.info(f"📊 Usage today: {usage_stats['daily_requests']}/{usage_stats['daily_limit']} ({usage_stats['percentage_used_today']}%)")
    except Exception as e:
        logger.error(f"❌ Could not get usage stats: {e}")
    
    set_webhook_on_startup()
    
    app.run(
        host="0.0.0.0",
        port=config.PORT,
        debug=config.DEBUG
    )
else:
    logger.info("🚀 Maya Secretary Bot starting via WSGI...")
    set_webhook_on_startup()
        
