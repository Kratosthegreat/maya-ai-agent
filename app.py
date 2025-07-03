"""
Maya Secretary Bot - Main Flask Application
Production-ready Telegram bot with advanced features
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from flask import Flask, request, jsonify
import requests
import httpx
from typing import Dict, Any, Optional
import re
import time
import threading

# Third-party imports
import google.generativeai as genai
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from cryptography.fernet import Fernet

# Local imports
from config import config

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO if not config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === FLASK APP SETUP ===
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# === DATABASE SETUP ===
Base = declarative_base()

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    username = Column(String(100))
    preferred_name = Column(String(100))
    language_code = Column(String(10), default="he")
    timezone = Column(String(50), default="Asia/Jerusalem")
    
    # Statistics
    total_messages = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    
    # Settings
    is_active = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    preferences = Column(JSON, default=dict)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    memories = relationship("UserMemory", back_populates="user")

class Conversation(Base):
    """Conversation history"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    message_type = Column(String(50), default="text")
    
    # Relationships
    user = relationship("User", back_populates="conversations")

class UserMemory(Base):
    """User memory and important information"""
    __tablename__ = "user_memory"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    memory_type = Column(String(50), default="general")
    importance = Column(Integer, default=5)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="memories")

# Database setup
engine = create_engine(config.DATABASE_URL, echo=config.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# === SECURITY & ENCRYPTION ===
class SecurityService:
    """Security service for rate limiting and encryption"""
    
    def __init__(self):
        self.fernet = Fernet(config.ENCRYPTION_KEY.encode()[:44] + b'=')
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
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return ""

security = SecurityService()

# === AI SERVICE ===
class AIService:
    """AI service for generating responses"""
    
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            config.GEMINI_MODEL,
            system_instruction=self._get_system_instruction()
        )
        self.chat_sessions = {}
    
    def _get_system_instruction(self) -> str:
        """Get system instruction for AI"""
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
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
            
            enhanced_message = f"""
            הודעת המשתמש: {message}
            הקשר: {context}
            השעה: {datetime.now().strftime('%H:%M')}
            """
            
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
    
    def get_or_create_user(self, telegram_data: Dict[str, Any]) -> User:
        """Get or create user"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == str(telegram_data.get('id'))).first()
            
            if not user:
                user = User(
                    telegram_id=str(telegram_data.get('id')),
                    first_name=telegram_data.get('first_name', ''),
                    last_name=telegram_data.get('last_name', ''),
                    username=telegram_data.get('username', ''),
                    language_code=telegram_data.get('language_code', 'he')
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"Created new user: {user.telegram_id}")
            
            return user
        finally:
            db.close()
    
    def update_user_activity(self, user_id: int):
        """Update user activity"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_activity = datetime.utcnow()
                user.total_messages += 1
                db.commit()
        finally:
            db.close()
    
    def get_user_context(self, user_id: int) -> str:
        """Get user context for AI"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return ""
            
            memories = db.query(UserMemory).filter(
                UserMemory.user_id == user_id
            ).order_by(UserMemory.importance.desc()).limit(5).all()
            
            context = f"""
            משתמש: {user.preferred_name or user.first_name or 'חבר/ה'}
            הודעות: {user.total_messages}
            זיכרונות: {', '.join([m.content for m in memories]) if memories else 'אין'}
            """
            
            return context
        finally:
            db.close()
    
    def add_memory(self, user_id: int, content: str, importance: int = 5):
        """Add user memory"""
        db = SessionLocal()
        try:
            memory = UserMemory(
                user_id=user_id,
                content=content,
                importance=importance
            )
            db.add(memory)
            db.commit()
        finally:
            db.close()

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
            user_data = message.get("from", {})
            text = message.get("text", "")
            
            # Rate limiting
            if security.is_rate_limited(str(user_data.get("id", 0))):
                self.send_message(chat_id, "⚠️ יותר מדי בקשות. המתן דקה ונסה שוב.")
                return
            
            # Get or create user
            user = user_service.get_or_create_user(user_data)
            user_service.update_user_activity(user.id)
            
            # Handle commands
            if text.startswith('/'):
                self._handle_command(chat_id, text, user)
            else:
                self._handle_message(chat_id, text, user)
                
        except Exception as e:
            logger.error(f"Process update error: {e}")
    
    def _handle_command(self, chat_id: int, command: str, user: User):
        """Handle bot commands"""
        cmd = command.split()[0].lower()
        
        if cmd == "/start":
            response = f"🌟 שלום {user.first_name}! אני מאיה, המזכירה שלך!\n\nאיך אוכל לעזור לך היום? 😊"
        
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
            context = user_service.get_user_context(user.id)
            response = f"🧠 הנה מה שאני זוכרת עליך:\n\n{context}"
        
        elif cmd == "/weather":
            city = weather_service.extract_city(command)
            response = weather_service.get_weather(city)
        
        elif cmd == "/stats":
            db = SessionLocal()
            try:
                total_users = db.query(User).count()
                total_conversations = db.query(Conversation).count()
                response = f"📊 סטטיסטיקות:\n👥 משתמשים: {total_users}\n💬 שיחות: {total_conversations}\n🤖 אני פעילה!"
            finally:
                db.close()
        
        elif cmd == "/forget":
            db = SessionLocal()
            try:
                db.query(UserMemory).filter(UserMemory.user_id == user.id).delete()
                db.query(Conversation).filter(Conversation.user_id == user.id).delete()
                db.commit()
                response = "🗑️ מחקתי הכל! נתחיל מחדש."
            finally:
                db.close()
        
        else:
            response = "❓ לא מכירה את הפקודה הזו. כתוב /help לעזרה."
        
        self.send_message(chat_id, response)
    
    def _handle_message(self, chat_id: int, text: str, user: User):
        """Handle regular messages"""
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
            user_service.add_memory(user.id, text, 8)
            context = user_service.get_user_context(user.id)
            response = ai_service.generate_response(user.telegram_id, text, context)
        
        # Regular AI response
        else:
            context = user_service.get_user_context(user.id)
            response = ai_service.generate_response(user.telegram_id, text, context)
        
        # Log conversation
        db = SessionLocal()
        try:
            conversation = Conversation(
                user_id=user.id,
                message=text,
                response=response
            )
            db.add(conversation)
            db.commit()
        finally:
            db.close()
        
        self.send_message(chat_id, response)

bot = TelegramBot()

# === FLASK ROUTES ===
@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Maya Secretary Bot",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": config.ENVIRONMENT
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
    db = SessionLocal()
    try:
        stats = {
            "total_users": db.query(User).count(),
            "active_users": db.query(User).filter(User.is_active == True).count(),
            "total_conversations": db.query(Conversation).count(),
            "bot_status": "active",
            "database_status": "connected"
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": "Stats unavailable"}), 500
    finally:
        db.close()

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
    logger.info("🚀 Starting Maya Secretary Bot...")
    logger.info(f"🌍 Environment: {config.ENVIRONMENT}")
    logger.info(f"🔗 Database: {config.DATABASE_URL.split('@')[0] if '@' in config.DATABASE_URL else config.DATABASE_URL}")
    
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
