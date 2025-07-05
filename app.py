# -*- coding: utf-8 -*-

# === Maya AI Secretary Bot 6.0 - Enhanced Intelligence Version ===

import os
import json
import re
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import pytz
import sqlite3
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
from contextlib import contextmanager

from flask import Flask, request, jsonify

# === Enhanced Configuration ===

class Config:
def **init**(self):
self.TELEGRAM_TOKEN = os.getenv(‘TELEGRAM_TOKEN’)
if not self.TELEGRAM_TOKEN:
raise ValueError(“Missing TELEGRAM_TOKEN environment variable”)

```
    self.PORT = int(os.getenv('PORT', 10000))
    self.DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    self.TIMEZONE = pytz.timezone('Asia/Jerusalem')
    self.WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
    self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    self.WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"
    self.DB_PATH = os.getenv('DB_PATH', 'maya_bot.db')
    self.WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '')
    self.MAX_CONVERSATION_HISTORY = 50
```

config = Config()

# === Data Models ===

class MessageType(Enum):
GREETING = “greeting”
QUESTION = “question”
TASK_REQUEST = “task_request”
WEATHER_REQUEST = “weather_request”
TIME_REQUEST = “time_request”
PERSONAL_INFO = “personal_info”
CASUAL_CHAT = “casual_chat”
UNKNOWN = “unknown”

@dataclass
class UserContext:
user_id: int
name: Optional[str] = None
preferred_language: str = ‘he’
location: Optional[str] = None
conversation_history: List[Dict] = None
preferences: Dict = None
last_activity: datetime = None

```
def __post_init__(self):
    if self.conversation_history is None:
        self.conversation_history = []
    if self.preferences is None:
        self.preferences = {}
```

# === Enhanced Logging ===

logging.basicConfig(
level=logging.DEBUG if config.DEBUG else logging.INFO,
format=’%(asctime)s - %(name)s - %(levelname)s - %(message)s’
)
logger = logging.getLogger(**name**)

app = Flask(**name**)

# === Database Manager ===

class DatabaseManager:
def **init**(self, db_path: str):
self.db_path = db_path
self.init_database()

```
def init_database(self):
    with self.get_connection() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                preferred_language TEXT DEFAULT 'he',
                location TEXT,
                preferences TEXT,
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
            
            CREATE TABLE IF NOT EXISTS user_context (
                user_id INTEGER PRIMARY KEY,
                context_data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
        ''')

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
```

# === Enhanced Intelligence Engine ===

class IntelligenceEngine:
def **init**(self):
self.hebrew_patterns = self._load_hebrew_patterns()
self.context_weights = {
‘name_mentioned’: 2.0,
‘previous_topic’: 1.5,
‘time_context’: 1.2,
‘location_context’: 1.3
}

```
def _load_hebrew_patterns(self) -> Dict[MessageType, List[str]]:
    return {
        MessageType.GREETING: [
            r'שלום|היי|הי|הייי|שלום עליכם|בוקר טוב|ערב טוב|לילה טוב',
            r'מה שלומך|מה נשמע|איך הולך|מה קורה'
        ],
        MessageType.WEATHER_REQUEST: [
            r'מזג אוויר|טמפרטורה|חם|קר|גשם|שמש|עננים|רוח',
            r'איך מזג האוויר|מה הטמפרטורה|האם יורד גשם'
        ],
        MessageType.TIME_REQUEST: [
            r'מה השעה|איזה יום|באיזה תאריך|מתי|זמן|שעה',
            r'יום (הולדת|נישואין)|מועד|לוח שנה'
        ],
        MessageType.PERSONAL_INFO: [
            r'שמי|קוראים לי|השם שלי|אני|גר ב|גרה ב|מ[בהמ]',
            r'בן \d+|בת \d+|אוהב|אוהבת|עובד|עובדת'
        ],
        MessageType.TASK_REQUEST: [
            r'תוכל|תוכלי|עזור|עזרי|בצע|תעשה|תעשי',
            r'אפשר|ניתן|רוצה ש|צריך ש|בקש|מבקש'
        ],
        MessageType.CASUAL_CHAT: [
            r'איך אתה|איך את|מה דעתך|מה חושב|מה חושבת',
            r'נחמד|יפה|טוב|רע|מעצבן|כיף|מעניין'
        ]
    }

def classify_message(self, text: str, context: UserContext) -> MessageType:
    text_lower = text.lower()
    scores = {}
    
    for msg_type, patterns in self.hebrew_patterns.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, text_lower):
                score += 1
        
        # Add context-based scoring
        if context.conversation_history:
            last_msg = context.conversation_history[-1]
            if 'type' in last_msg and last_msg['type'] == msg_type.value:
                score += self.context_weights['previous_topic']
        
        scores[msg_type] = score
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else MessageType.UNKNOWN

def extract_entities(self, text: str) -> Dict[str, Any]:
    entities = {}
    
    # Extract names
    name_patterns = [
        r'שמי (הוא )?(.+?)(?:\s|$|\.)',
        r'קוראים לי (.+?)(?:\s|$|\.)',
        r'השם שלי (הוא )?(.+?)(?:\s|$|\.)',
        r'אני (.+?)(?:\s|$|\.)'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            entities['name'] = match.group(-1).strip()
            break
    
    # Extract locations
    israeli_cities = [
        'תל אביב', 'ירושלים', 'חיפה', 'באר שבע', 'נתניה', 'פתח תקווה',
        'אשדוד', 'ראשון לציון', 'אשקלון', 'רמת גן', 'הרצליה', 'כפר סבא',
        'רעננה', 'הוד השרון', 'רמת השרון', 'גבעתיים', 'בת ים', 'עפולה'
    ]
    
    for city in israeli_cities:
        if city in text:
            entities['location'] = city
            break
    
    # Extract time references
    time_patterns = [
        r'בשעה (\d{1,2}):?(\d{2})?',
        r'ב(\d{1,2}) בבוקר|בערב|בלילה',
        r'(מחר|אתמול|היום|מחרתיים)'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            entities['time_reference'] = match.group(0)
            break
    
    return entities
```

# === Enhanced Services ===

class WeatherService:
def **init**(self):
self.api_key = config.WEATHER_API_KEY
self.cache = {}
self.cache_duration = 600  # 10 minutes

```
def get_weather_info(self, city: str = 'Israel') -> Optional[Dict[str, Any]]:
    if not self.api_key:
        return None
    
    cache_key = f"weather_{city}"
    if cache_key in self.cache:
        cached_data, timestamp = self.cache[cache_key]
        if datetime.now().timestamp() - timestamp < self.cache_duration:
            return cached_data
    
    try:
        response = requests.get(
            f"{config.WEATHER_API_URL}?key={self.api_key}&q={city}&aqi=yes",
            timeout=5
        )
        data = response.json()
        
        weather_info = {
            'temperature': data['current']['temp_c'],
            'condition': data['current']['condition']['text'],
            'humidity': data['current']['humidity'],
            'wind_speed': data['current']['wind_kph'],
            'feels_like': data['current']['feelslike_c'],
            'uv_index': data['current']['uv'],
            'city': data['location']['name']
        }
        
        self.cache[cache_key] = (weather_info, datetime.now().timestamp())
        return weather_info
        
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None
```

class AIResponseGenerator:
def **init**(self):
self.openai_api_key = config.OPENAI_API_KEY
self.personality_prompt = “””
אתה מאיה, עוזרת אישית חכמה ומזמינה שמדברת בעברית.
אתה עוזרת לאנשים במגוון משימות ותמיד מנסה להיות שימושית וידידותית.
תמיד תענה בעברית, תהיה אדיבה ומקצועית.
אם אתה לא בטוחה במשהו, תגידי זאת בכנות.
“””

```
def generate_contextual_response(self, message: str, context: UserContext, 
                               message_type: MessageType, entities: Dict) -> str:
    # If no OpenAI API, use rule-based responses
    if not self.openai_api_key:
        return self._generate_rule_based_response(message, context, message_type, entities)
    
    try:
        # Build context string
        context_str = self._build_context_string(context, entities)
        
        prompt = f"""
        {self.personality_prompt}
        
        הקשר על המשתמש: {context_str}
        סוג ההודעה: {message_type.value}
        הודעת המשתמש: "{message}"
        
        אנא ענה בצורה מתאימה ושימושית.
        """
        
        # Here you would call OpenAI API
        # For now, fall back to rule-based
        return self._generate_rule_based_response(message, context, message_type, entities)
        
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return self._generate_rule_based_response(message, context, message_type, entities)

def _build_context_string(self, context: UserContext, entities: Dict) -> str:
    context_parts = []
    
    if context.name:
        context_parts.append(f"השם: {context.name}")
    if context.location:
        context_parts.append(f"מיקום: {context.location}")
    if context.conversation_history:
        last_topics = [msg.get('type', '') for msg in context.conversation_history[-3:]]
        context_parts.append(f"נושאים אחרונים: {', '.join(last_topics)}")
    
    return ' | '.join(context_parts) if context_parts else "אין הקשר קודם"

def _generate_rule_based_response(self, message: str, context: UserContext, 
                                message_type: MessageType, entities: Dict) -> str:
    name = context.name or entities.get('name', '')
    greeting_suffix = f" {name}" if name else ""
    
    responses = {
        MessageType.GREETING: [
            f"שלום{greeting_suffix}! איך אוכל לעזור לך היום? 😊",
            f"היי{greeting_suffix}! מה שלומך? איך יכולה לסייע?",
            f"שמחה לראות אותך{greeting_suffix}! במה אוכל לעזור?"
        ],
        MessageType.WEATHER_REQUEST: self._handle_weather_response(entities),
        MessageType.TIME_REQUEST: self._handle_time_response(),
        MessageType.PERSONAL_INFO: self._handle_personal_info(entities, context),
        MessageType.TASK_REQUEST: [
            f"בוודאי{greeting_suffix}! איך בדיוק אוכל לעזור לך?",
            "אשמח לסייע! תוכל להסביר יותר על מה שאתה צריך?"
        ],
        MessageType.CASUAL_CHAT: [
            f"מעניין{greeting_suffix}! מה דעתך על זה?",
            "נחמד לשמוע! ספר לי עוד."
        ]
    }
    
    if message_type in responses:
        response_list = responses[message_type]
        if isinstance(response_list, list):
            import random
            return random.choice(response_list)
        return response_list
    
    return f"מעניין{greeting_suffix}! תוכל להסביר יותר? אני כאן לעזור 🤗"

def _handle_weather_response(self, entities: Dict) -> str:
    location = entities.get('location', 'Israel')
    weather_service = WeatherService()
    weather_info = weather_service.get_weather_info(location)
    
    if weather_info:
        return (f"🌤️ מזג האוויר ב{weather_info['city']}:\n"
               f"🌡️ טמפרטורה: {weather_info['temperature']}°C "
               f"(מרגיש כמו {weather_info['feels_like']}°C)\n"
               f"☁️ מצב: {weather_info['condition']}\n"
               f"💧 לחות: {weather_info['humidity']}%\n"
               f"🌪️ רוח: {weather_info['wind_speed']} קמ\"ש")
    
    return f"לא מצליחה לקבל נתוני מזג אוויר עבור {location} כרגע. נסה שוב מאוחר יותר 🚧"

def _handle_time_response(self) -> str:
    now = datetime.now(config.TIMEZONE)
    hebrew_days = {
        'Monday': 'שני', 'Tuesday': 'שלישי', 'Wednesday': 'רביעי',
        'Thursday': 'חמישי', 'Friday': 'שישי', 'Saturday': 'שבת', 'Sunday': 'ראשון'
    }
    day_name = hebrew_days.get(now.strftime('%A'), now.strftime('%A'))
    
    return (f"📅 היום יום {day_name}, {now.strftime('%d/%m/%Y')}\n"
           f"🕒 השעה: {now.strftime('%H:%M')}")

def _handle_personal_info(self, entities: Dict, context: UserContext) -> str:
    if 'name' in entities:
        return f"נעים מאוד להכיר אותך, {entities['name']}! 😊 איך אוכל לעזור לך?"
    if 'location' in entities:
        return f"נחמד! אז אתה מ{entities['location']}. מקום יפה! 🏘️"
    return "תודה שאתה חולק איתי! זה עוזר לי להכיר אותך יותר טוב 💝"
```

# === Enhanced User Management ===

class EnhancedUserMemory:
def **init**(self, db_manager: DatabaseManager):
self.db = db_manager
self.active_users = {}

```
def get_user_context(self, user_id: int) -> UserContext:
    if user_id in self.active_users:
        return self.active_users[user_id]
    
    with self.db.get_connection() as conn:
        user_row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        
        if user_row:
            preferences = json.loads(user_row['preferences'] or '{}')
            context = UserContext(
                user_id=user_id,
                name=user_row['name'],
                preferred_language=user_row['preferred_language'],
                location=user_row['location'],
                preferences=preferences,
                last_activity=datetime.fromisoformat(user_row['last_activity'])
            )
        else:
            context = UserContext(user_id=user_id, last_activity=datetime.now())
            self._create_user(context)
        
        # Load conversation history
        history_rows = conn.execute(
            """SELECT message, response, message_type, timestamp 
               FROM conversations WHERE user_id = ? 
               ORDER BY timestamp DESC LIMIT ?""",
            (user_id, config.MAX_CONVERSATION_HISTORY)
        ).fetchall()
        
        context.conversation_history = [
            {
                'message': row['message'],
                'response': row['response'],
                'type': row['message_type'],
                'timestamp': row['timestamp']
            }
            for row in reversed(history_rows)
        ]
    
    self.active_users[user_id] = context
    return context

def update_user_context(self, context: UserContext):
    with self.db.get_connection() as conn:
        conn.execute(
            """UPDATE users SET name = ?, location = ?, preferences = ?, 
               last_activity = CURRENT_TIMESTAMP WHERE user_id = ?""",
            (context.name, context.location, 
             json.dumps(context.preferences), context.user_id)
        )
    
    self.active_users[context.user_id] = context

def save_conversation(self, user_id: int, message: str, response: str, message_type: MessageType):
    with self.db.get_connection() as conn:
        conn.execute(
            """INSERT INTO conversations (user_id, message, response, message_type)
               VALUES (?, ?, ?, ?)""",
            (user_id, message, response, message_type.value)
        )

def _create_user(self, context: UserContext):
    with self.db.get_connection() as conn:
        conn.execute(
            """INSERT INTO users (user_id, name, preferred_language, location, preferences)
               VALUES (?, ?, ?, ?, ?)""",
            (context.user_id, context.name, context.preferred_language,
             context.location, json.dumps(context.preferences))
        )
```

# === Enhanced Telegram Bot ===

class EnhancedTelegramBot:
def **init**(self):
self.token = config.TELEGRAM_TOKEN
self.api_url = f”https://api.telegram.org/bot{self.token}”
self.db_manager = DatabaseManager(config.DB_PATH)
self.memory = EnhancedUserMemory(self.db_manager)
self.intelligence = IntelligenceEngine()
self.ai_generator = AIResponseGenerator()

```
def verify_webhook(self, request_data: bytes, signature: str) -> bool:
    if not config.WEBHOOK_SECRET:
        return True  # Skip verification if no secret set
    
    expected_signature = hmac.new(
        config.WEBHOOK_SECRET.encode(),
        request_data,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def send_message(self, chat_id: int, text: str, 
                reply_markup: Optional[Dict] = None) -> bool:
    try:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        response = requests.post(
            f"{self.api_url}/sendMessage",
            json=payload,
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
    
    # Get user context
    context = self.memory.get_user_context(user_id)
    
    # Classify message and extract entities
    message_type = self.intelligence.classify_message(text, context)
    entities = self.intelligence.extract_entities(text)
    
    # Update context with extracted entities
    if 'name' in entities and entities['name']:
        context.name = entities['name']
    if 'location' in entities and entities['location']:
        context.location = entities['location']
    
    # Generate intelligent response
    response = self.ai_generator.generate_contextual_response(
        text, context, message_type, entities
    )
    
    # Save conversation and update context
    self.memory.save_conversation(user_id, text, response, message_type)
    self.memory.update_user_context(context)
    
    return response

def process_update(self, update: Dict[str, Any]):
    if "message" not in update:
        return
    
    message = update["message"]
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    logger.info(f"Processing enhanced message from user {user_id}")
    
    try:
        response = self.process_message(message)
        if response:
            success = self.send_message(chat_id, response)
            if not success:
                logger.error(f"Failed to send response to user {user_id}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        self.send_message(chat_id, "מצטערת, הייתה בעיה טכנית. נסה שוב בעוד רגע 🔧")
```

# === Enhanced Flask Routes ===

@app.route(’/’)
def home():
return jsonify({
“status”: “running”,
“service”: “Maya AI Bot”,
“version”: “6.0”,
“features”: [
“Advanced Hebrew NLP”,
“User Context Management”,
“Intelligent Conversation”,
“Persistent Memory”,
“Enhanced Weather Service”
],
“timestamp”: datetime.now().isoformat()
})

@app.route(’/webhook’, methods=[‘POST’])
def webhook():
if request.method == ‘POST’:
try:
# Verify webhook signature
signature = request.headers.get(‘X-Telegram-Bot-Api-Secret-Token’, ‘’)
if not bot.verify_webhook(request.data, signature):
logger.warning(“Invalid webhook signature”)
return jsonify({“status”: “error”, “message”: “Invalid signature”}), 403

```
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
```

@app.route(’/stats’)
def stats():
try:
with bot.db_manager.get_connection() as conn:
user_count = conn.execute(“SELECT COUNT(*) FROM users”).fetchone()[0]
message_count = conn.execute(“SELECT COUNT(*) FROM conversations”).fetchone()[0]

```
    return jsonify({
        "users": user_count,
        "messages": message_count,
        "active_sessions": len(bot.memory.active_users)
    })
except Exception as e:
    return jsonify({"error": str(e)}), 500
```

# === Initialization ===

bot = EnhancedTelegramBot()

if **name** == ‘**main**’:
logger.info(f”Starting Enhanced Maya AI Bot on port {config.PORT}”)
logger.info(f”Features: Context-aware conversations, Persistent memory, Advanced NLP”)
app.run(host=‘0.0.0.0’, port=config.PORT, debug=config.DEBUG)