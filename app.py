# -*- coding: utf-8 -*-
# Maya AI Secretary Bot 6.0 - Clean Version
import os
import json
import re
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
import pytz
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import random

from flask import Flask, request, jsonify

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
        self.WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"
        self.DB_PATH = os.getenv("DB_PATH", "maya_bot.db")
        self.MAX_CONVERSATION_HISTORY = 20

# Data Models
class MessageType(Enum):
    GREETING = "greeting"
    WEATHER_REQUEST = "weather_request"
    TIME_REQUEST = "time_request"
    PERSONAL_INFO = "personal_info"
    TASK_REQUEST = "task_request"
    CASUAL_CHAT = "casual_chat"
    UNKNOWN = "unknown"

@dataclass
class UserContext:
    user_id: int
    name: Optional[str] = None
    location: Optional[str] = None
    conversation_history: List[Dict] = field(default_factory=list)
    last_activity: Optional[datetime] = None

# Initialize config
config = Config()

# Logging
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database Manager
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        try:
            with self.get_connection() as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        name TEXT,
                        location TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        message TEXT,
                        response TEXT,
                        message_type TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    );
                """)
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

# Intelligence Engine
class IntelligenceEngine:
    def __init__(self):
        self.hebrew_patterns = {
            MessageType.GREETING: [
                r"שלום|היי|הי|הייי|בוקר טוב|ערב טוב|לילה טוב",
                r"מה שלומך|מה נשמע|איך הולך|מה קורה"
            ],
            MessageType.WEATHER_REQUEST: [
                r"מזג אוויר|טמפרטורה|חם|קר|גשם|שמש|עננים",
                r"איך מזג האוויר|מה הטמפרטורה"
            ],
            MessageType.TIME_REQUEST: [
                r"מה השעה|איזה יום|באיזה תאריך|זמן|שעה",
                r"יום.*|מועד|לוח שנה"
            ],
            MessageType.PERSONAL_INFO: [
                r"שמי|קוראים לי|השם שלי|אני.*|גר ב|גרה ב",
                r"אוהב|אוהבת|עובד|עובדת"
            ],
            MessageType.TASK_REQUEST: [
                r"תוכל|תוכלי|עזור|עזרי|בצע|תעשה|תעשי",
                r"אפשר|רוצה ש|צריך ש|בקש"
            ],
            MessageType.CASUAL_CHAT: [
                r"איך את|מה דעתך|מה חושב|נחמד|יפה|טוב|רע"
            ]
        }
    
    def classify_message(self, text: str) -> MessageType:
        text_lower = text.lower()
        scores = {}
        
        for msg_type, patterns in self.hebrew_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1
            scores[msg_type] = score
        
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            return max(scores, key=scores.get)
        return MessageType.UNKNOWN
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        entities = {}
        
        # Extract names
        name_patterns = [
            r"שמי (הוא )?(.+?)(?:\s|$|\.)",
            r"קוראים לי (.+?)(?:\s|$|\.)",
            r"השם שלי (הוא )?(.+?)(?:\s|$|\.)",
            r"אני (.+?)(?:\s|$|\.)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(-1).strip()
                if len(name) > 0 and len(name) < 20:
                    entities["name"] = name
                break
        
        # Extract locations
        israeli_cities = [
            "תל אביב", "ירושלים", "חיפה", "באר שבע", "נתניה", 
            "פתח תקווה", "אשדוד", "ראשון לציון", "עפולה"
        ]
        
        for city in israeli_cities:
            if city in text:
                entities["location"] = city
                break
        
        return entities

# Weather Service
class WeatherService:
    def __init__(self):
        self.api_key = config.WEATHER_API_KEY
        self.cache = {}
        self.cache_duration = 600
    
    def get_weather_info(self, city: str = "Israel") -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        
        cache_key = f"weather_{city}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_duration:
                return cached_data
        
        try:
            response = requests.get(
                f"{config.WEATHER_API_URL}?key={self.api_key}&q={city}&aqi=no",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                weather_info = {
                    "temperature": data["current"]["temp_c"],
                    "condition": data["current"]["condition"]["text"],
                    "humidity": data["current"]["humidity"],
                    "feels_like": data["current"]["feelslike_c"],
                    "city": data["location"]["name"]
                }
                
                self.cache[cache_key] = (weather_info, datetime.now().timestamp())
                return weather_info
            
        except Exception as e:
            logger.error(f"Weather API error: {e}")
        
        return None

# Response Generator
class ResponseGenerator:
    def __init__(self):
        self.weather_service = WeatherService()
    
    def generate_response(self, message: str, context: UserContext, 
                         message_type: MessageType, entities: Dict) -> str:
        
        name = context.name or entities.get("name", "")
        greeting_suffix = f" {name}" if name else ""
        
        if message_type == MessageType.GREETING:
            greetings = [
                f"שלום{greeting_suffix}! איך אוכל לעזור לך היום? 😊",
                f"היי{greeting_suffix}! מה שלומך? איך יכולה לסייע?",
                f"שמחה לראות אותך{greeting_suffix}! במה אוכל לעזור?"
            ]
            return random.choice(greetings)
        
        elif message_type == MessageType.WEATHER_REQUEST:
            return self._handle_weather_response(entities)
        
        elif message_type == MessageType.TIME_REQUEST:
            return self._handle_time_response()
        
        elif message_type == MessageType.PERSONAL_INFO:
            return self._handle_personal_info(entities)
        
        elif message_type == MessageType.TASK_REQUEST:
            tasks = [
                f"בוודאי{greeting_suffix}! איך בדיוק אוכל לעזור לך?",
                "אשמח לסייע! תוכל להסביר יותר על מה שאתה צריך?",
                "כמובן! ספר לי מה אתה רוצה שאעשה."
            ]
            return random.choice(tasks)
        
        elif message_type == MessageType.CASUAL_CHAT:
            casual = [
                f"מעניין{greeting_suffix}! מה דעתך על זה?",
                "נחמד לשמוע! ספר לי עוד.",
                "זה נשמע כיף! איך זה הרגיש?"
            ]
            return random.choice(casual)
        
        else:
            defaults = [
                f"מעניין{greeting_suffix}! תוכל להסביר יותר?",
                "אני כאן לעזור! במה אוכל לסייע?",
                "לא בטוחה שהבנתי. תוכל לנסח אחרת?"
            ]
            return random.choice(defaults)
    
    def _handle_weather_response(self, entities: Dict) -> str:
        location = entities.get("location", "Israel")
        weather_info = self.weather_service.get_weather_info(location)
        
        if weather_info:
            return (f"🌤️ מזג האוויר ב{weather_info['city']}:\n"
                   f"🌡️ טמפרטורה: {weather_info['temperature']}°C "
                   f"(מרגיש כמו {weather_info['feels_like']}°C)\n"
                   f"☁️ מצב: {weather_info['condition']}\n"
                   f"💧 לחות: {weather_info['humidity']}%")
        
        return f"לא מצליחה לקבל נתוני מזג אוויר עבור {location} כרגע. נסה שוב מאוחר יותר 🚧"
    
    def _handle_time_response(self) -> str:
        now = datetime.now(config.TIMEZONE)
        hebrew_days = {
            "Monday": "שני", "Tuesday": "שלישי", "Wednesday": "רביעי",
            "Thursday": "חמישי", "Friday": "שישי", "Saturday": "שבת", "Sunday": "ראשון"
        }
        day_name = hebrew_days.get(now.strftime("%A"), now.strftime("%A"))
        
        return (f"📅 היום יום {day_name}, {now.strftime('%d/%m/%Y')}\n"
               f"🕒 השעה: {now.strftime('%H:%M')}")
    
    def _handle_personal_info(self, entities: Dict) -> str:
        if "name" in entities:
            return f"נעים מאוד להכיר אותך, {entities['name']}! 😊 איך אוכל לעזור לך?"
        if "location" in entities:
            return f"נחמד! אז אתה מ{entities['location']}. מקום יפה! 🏘️"
        return "תודה שאתה חולק איתי! זה עוזר לי להכיר אותך יותר טוב 💝"

# User Memory
class UserMemory:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.active_users = {}
    
    def get_user_context(self, user_id: int) -> UserContext:
        if user_id in self.active_users:
            return self.active_users[user_id]
        
        try:
            with self.db.get_connection() as conn:
                user_row = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                
                if user_row:
                    context = UserContext(
                        user_id=user_id,
                        name=user_row["name"],
                        location=user_row["location"],
                        last_activity=datetime.now()
                    )
                else:
                    context = UserContext(user_id=user_id, last_activity=datetime.now())
                    self._create_user(context)
                
                # Load recent conversation history
                history_rows = conn.execute(
                    """SELECT message, response, message_type, timestamp 
                       FROM conversations WHERE user_id = ? 
                       ORDER BY timestamp DESC LIMIT ?""",
                    (user_id, config.MAX_CONVERSATION_HISTORY)
                ).fetchall()
                
                context.conversation_history = [
                    {
                        "message": row["message"],
                        "response": row["response"],
                        "type": row["message_type"],
                        "timestamp": row["timestamp"]
                    }
                    for row in reversed(history_rows)
                ]
        
        except Exception as e:
            logger.error(f"Error loading user context: {e}")
            context = UserContext(user_id=user_id, last_activity=datetime.now())
        
        self.active_users[user_id] = context
        return context
    
    def update_user_context(self, context: UserContext):
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """UPDATE users SET name = ?, location = ?, 
                       last_activity = CURRENT_TIMESTAMP WHERE user_id = ?""",
                    (context.name, context.location, context.user_id)
                )
            self.active_users[context.user_id] = context
        except Exception as e:
            logger.error(f"Error updating user context: {e}")
    
    def save_conversation(self, user_id: int, message: str, response: str, message_type: MessageType):
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """INSERT INTO conversations (user_id, message, response, message_type)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, message, response, message_type.value)
                )
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def _create_user(self, context: UserContext):
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """INSERT INTO users (user_id, name, location)
                       VALUES (?, ?, ?)""",
                    (context.user_id, context.name, context.location)
                )
        except Exception as e:
            logger.error(f"Error creating user: {e}")

# Enhanced Telegram Bot
class EnhancedTelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.db_manager = DatabaseManager(config.DB_PATH)
        self.memory = UserMemory(self.db_manager)
        self.intelligence = IntelligenceEngine()
        self.response_generator = ResponseGenerator()
    
    def send_message(self, chat_id: int, text: str) -> bool:
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
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        text = message.get("text", "").strip()
        user_id = message["from"]["id"]
        
        if not text:
            return None
        
        try:
            # Get user context
            context = self.memory.get_user_context(user_id)
            
            # Classify message and extract entities
            message_type = self.intelligence.classify_message(text)
            entities = self.intelligence.extract_entities(text)
            
            # Update context with extracted entities
            if "name" in entities and entities["name"]:
                context.name = entities["name"]
            if "location" in entities and entities["location"]:
                context.location = entities["location"]
            
            # Generate response
            response = self.response_generator.generate_response(
                text, context, message_type, entities
            )
            
            # Save conversation and update context
            self.memory.save_conversation(user_id, text, response, message_type)
            self.memory.update_user_context(context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "מצטערת, הייתה בעיה טכנית. נסה שוב בעוד רגע 🔧"
    
    def process_update(self, update: Dict[str, Any]):
        if "message" not in update:
            return
        
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        
        logger.info(f"Processing message from user {user_id}")
        
        try:
            response = self.process_message(message)
            if response:
                success = self.send_message(chat_id, response)
                if not success:
                    logger.error(f"Failed to send response to user {user_id}")
        except Exception as e:
            logger.error(f"Error in process_update: {e}")
            self.send_message(chat_id, "מצטערת, הייתה בעיה. נסה שוב 🔧")

# Flask Routes
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "service": "Maya AI Bot",
        "version": "6.0",
        "features": [
            "Hebrew NLP",
            "User Memory", 
            "Weather Service",
            "Conversation History"
        ],
        "timestamp": datetime.now().isoformat()
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        try:
            update = request.get_json()
            if not update:
                logger.warning("Empty webhook update received")
                return jsonify({"status": "error", "message": "Empty request"}), 400
            
            bot.process_update(update)
            return jsonify({"status": "success"}), 200
            
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Method not allowed"}), 405

@app.route("/stats")
def stats():
    try:
        with bot.db_manager.get_connection() as conn:
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            message_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            
        return jsonify({
            "users": user_count,
            "messages": message_count,
            "active_sessions": len(bot.memory.active_users)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Initialization
bot = EnhancedTelegramBot()

if __name__ == "__main__":
    logger.info(f"Starting Enhanced Maya AI Bot on port {config.PORT}")
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
