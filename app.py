# -*- coding: utf-8 -*-
# Maya - Minimal Working Version
import os
import json
import re
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
import pytz
import random
import sqlite3
from dataclasses import dataclass, field
from contextlib import contextmanager
import wikipedia

from flask import Flask, request, jsonify, Response
from http import HTTPStatus

# Optional imports
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Configuration
class Config:
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        if not self.TELEGRAM_TOKEN:
            raise ValueError("Missing TELEGRAM_TOKEN environment variable")
        
        self.PORT = int(os.getenv("PORT", 10000))
        self.DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
        self.TIMEZONE = pytz.timezone("Asia/Jerusalem")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
        self.WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

config = Config()

# Logging
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Knowledge Engine
class MinimalKnowledgeEngine:
    def __init__(self):
        self.cache = {}
        self.gemini_model = None
        self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini if available"""
        if GEMINI_AVAILABLE and config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini Pro initialized")
            except Exception as e:
                logger.error(f"Gemini init error: {e}")
    
    async def get_answer(self, query: str) -> str:
        """Get answer using available sources"""
        
        # Try Wikipedia first
        try:
            wiki_results = wikipedia.search(query, results=3)
            if wiki_results:
                summary = wikipedia.summary(query, sentences=2)
                return f"📚 {summary}"
        except:
            pass
        
        # Try Gemini if available
        if self.gemini_model:
            try:
                prompt = f"ענה בעברית בצורה קצרה ומועילה: {query}"
                response = self.gemini_model.generate_content(prompt)
                if response and response.text:
                    return f"🤖 {response.text}"
            except Exception as e:
                logger.error(f"Gemini error: {e}")
        
        # Fallback responses
        fallback_responses = [
            "מעניין! אני מחפשת מידע על זה. תוכל לנסח את השאלה קצת אחרת?",
            "זה נושא מעניין! אני עדיין לומדת עליו. יש לך שאלה ספציפית יותר?",
            "אני כאן לעזור! תוכל לתת לי יותר פרטים על מה שאתה מחפש?"
        ]
        return random.choice(fallback_responses)

# Conversation Engine  
class SimpleConversationEngine:
    def __init__(self):
        self.knowledge_engine = MinimalKnowledgeEngine()
        self.user_names = {}
    
    async def process_message(self, user_id: int, message: str) -> str:
        """Process message and return response"""
        message_lower = message.lower().strip()
        
        # Handle name introduction
        name_patterns = [
            r'שמי (הוא )?(.+?)(?:\s|$|\.)',
            r'קוראים לי (.+?)(?:\s|$|\.)',
            r'השם שלי (הוא )?(.+?)(?:\s|$|\.)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(-1).strip()
                if len(name) > 0 and len(name) < 20:
                    self.user_names[user_id] = name
                    return f"נעים מאוד להכיר אותך, {name}! 😊 אני מאיה, העוזרת הדיגיטלית שלך. איך אוכל לעזור?"
        
        # Handle greetings
        greetings = ['שלום', 'היי', 'הי', 'הייי', 'בוקר טוב', 'ערב טוב', 'לילה טוב']
        if any(greeting in message_lower for greeting in greetings):
            user_name = self.user_names.get(user_id, "")
            name_suffix = f" {user_name}" if user_name else ""
            
            now = datetime.now(config.TIMEZONE)
            hour = now.hour
            
            if 5 <= hour < 12:
                base_greeting = f"בוקר טוב{name_suffix}! ☀️ איך התחלת את היום?"
            elif 12 <= hour < 17:
                base_greeting = f"צהריים טובים{name_suffix}! 🌤️ איך עובר היום?"
            elif 17 <= hour < 22:
                base_greeting = f"ערב טוב{name_suffix}! 🌆 איך היה היום?"
            else:
                base_greeting = f"לילה טוב{name_suffix}! 🌙 עדיין ער/ה?"
            
            return base_greeting + " איך אוכל לעזור לך?"
        
        # Handle time requests
        time_keywords = ['מה השעה', 'איזה יום', 'תאריך', 'זמן', 'שעה']
        if any(keyword in message_lower for keyword in time_keywords):
            now = datetime.now(config.TIMEZONE)
            hebrew_days = {
                'Monday': 'שני', 'Tuesday': 'שלישי', 'Wednesday': 'רביעי',
                'Thursday': 'חמישי', 'Friday': 'שישי', 'Saturday': 'שבת', 'Sunday': 'ראשון'
            }
            day_name = hebrew_days.get(now.strftime('%A'), now.strftime('%A'))
            return f"📅 היום יום {day_name}, {now.strftime('%d/%m/%Y')}\n🕒 השעה: {now.strftime('%H:%M')}"
        
        # Handle weather requests
        weather_keywords = ['מזג אוויר', 'טמפרטורה', 'חם', 'קר', 'גשם', 'שמש']
        if any(keyword in message_lower for keyword in weather_keywords):
            return await self._handle_weather(message)
        
        # Handle gratitude
        thanks_words = ['תודה', 'מעריך', 'תודה רבה']
        if any(word in message_lower for word in thanks_words):
            responses = [
                "😊 בכיף! תמיד נעים לעזור!",
                "🙏 בבקשה! זה משמח אותי!",
                "❤️ שמחה שיכולתי לעזור!"
            ]
            return random.choice(responses)
        
        # Default - use knowledge engine
        return await self.knowledge_engine.get_answer(message)
    
    async def _handle_weather(self, message: str) -> str:
        """Handle weather requests"""
        if not config.WEATHER_API_KEY:
            return "🌤️ שירות מזג אוויר לא זמין כרגע. אפשר להוסיף WEATHER_API_KEY?"
        
        # Extract city
        cities = ['תל אביב', 'ירושלים', 'חיפה', 'באר שבע', 'Tel Aviv', 'Jerusalem', 'Haifa']
        city = 'Tel Aviv'  # default
        for c in cities:
            if c.lower() in message.lower():
                city = c
                break
        
        try:
            response = requests.get(
                config.WEATHER_API_URL,
                params={
                    'q': city,
                    'appid': config.WEATHER_API_KEY,
                    'units': 'metric'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                
                return (f"🌤️ מזג האוויר ב{data['name']}:\n"
                       f"🌡️ טמפרטורה: {temp:.1f}°C\n"
                       f"☁️ מצב: {description}\n"
                       f"💧 לחות: {humidity}%")
            
        except Exception as e:
            logger.error(f"Weather error: {e}")
        
        return f"🌤️ לא הצלחתי לקבל מידע על מזג האוויר ב{city} כרגע."

# Main Bot
class MayaBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.conversation_engine = SimpleConversationEngine()
    
    def send_message(self, chat_id: int, text: str) -> bool:
        """Send message to Telegram"""
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
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    async def process_update(self, update: Dict[str, Any]):
        """Process Telegram update"""
        try:
            if "message" not in update:
                return
            
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "").strip()
            user_id = message.get("from", {}).get("id")
            
            if not chat_id or not text or not user_id:
                return
            
            logger.info(f"Processing message from {user_id}: {text[:50]}...")
            
            # Generate response
            response = await self.conversation_engine.process_message(user_id, text)
            
            # Send response
            success = self.send_message(chat_id, response)
            if not success:
                self.send_message(chat_id, "😅 הייתה בעיה קטנה. תוכל לנסות שוב?")
        
        except Exception as e:
            logger.error(f"Process update error: {e}")

# Flask Routes
bot = MayaBot()

@app.route("/", methods=["GET"])
def home():
    """Home page"""
    return jsonify({
        "status": "🤖 Maya Bot - Working!",
        "version": "Minimal 1.0",
        "features": [
            "🧠 Gemini AI Integration" if GEMINI_AVAILABLE else "📚 Wikipedia Knowledge",
            "🌤️ Weather Information",
            "🕐 Time & Date",
            "💬 Smart Conversation",
            "👤 User Memory"
        ],
        "gemini_status": "✅ Active" if GEMINI_AVAILABLE and config.GEMINI_API_KEY else "❌ Not configured",
        "weather_status": "✅ Active" if config.WEATHER_API_KEY else "❌ Not configured",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Telegram webhook"""
    try:
        update = request.get_json()
        if not update:
            return Response(status=HTTPStatus.BAD_REQUEST)
        
        # Process asynchronously
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.process_update(update))
        loop.close()
        
        return Response(status=HTTPStatus.OK)
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route("/test", methods=["GET"])
def test():
    """Test endpoint"""
    return jsonify({
        "message": "Maya is working!",
        "test_queries": [
            "היי מאיה",
            "מה השעה",
            "שמי דוד",
            "מה מזג האוויר",
            "ספר לי על פייתון"
        ]
    })

# Run the app
if __name__ == "__main__":
    logger.info("🚀 Starting Maya Bot - Minimal Version")
    logger.info(f"🌐 Port: {config.PORT}")
    logger.info(f"🤖 Gemini: {'✅' if GEMINI_AVAILABLE and config.GEMINI_API_KEY else '❌'}")
    logger.info(f"🌤️ Weather: {'✅' if config.WEATHER_API_KEY else '❌'}")
    
    app.run(
        host="0.0.0.0",
        port=config.PORT,
        debug=config.DEBUG
    )
