# -*- coding: utf-8 -*-
# === Maya Secretary Bot 4.0 - Production Ready ===
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
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dateutil.parser import parse

# === Configuration ===
class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
    MAX_REQUESTS_PER_MINUTE = 20
    GEMINI_MODEL = "gemini-1.5-flash"
    SECURE_STORAGE_PATH = "secure_tokens/"

config = Config()

# === Logging ===
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')

# === Enhanced Memory System ===
class EnhancedMemory:
    def __init__(self, user_id):
        self.user_id = user_id
        self.memory_file = f"users/{user_id}_memory.json"
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        self.load_memory()
    
    def load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = {
                    "personal_details": {},
                    "preferences": {},
                    "conversation_history": []
                }
        except Exception as e:
            logger.error(f"Memory load error: {e}")
            self.data = {
                "personal_details": {},
                "preferences": {},
                "conversation_history": []
            }
    
    def save_memory(self):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Memory save error: {e}")
    
    def extract_personal_info(self, text):
        text_lower = text.lower()
        # Name detection
        name_patterns = [r"קוראים לי (.+)", r"שמי (.+)", r"השם שלי (.+)"]
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match and len(match.group(1).split()) < 4:
                self.data["personal_details"]["name"] = match.group(1).strip()
                self.save_memory()
        
        # Birthday detection
        if any(x in text_lower for x in ["נולדתי ב", "תאריך לידה"]):
            self.data["personal_details"]["birthday"] = text.split("ב")[-1].strip()
            self.save_memory()

# === Google Integration ===
class GoogleIntegration:
    def __init__(self, user_id):
        self.user_id = user_id
        self.token_file = f"{config.SECURE_STORAGE_PATH}user_{user_id}_token.json"
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
    
    def get_credentials(self):
        if os.path.exists(self.token_file):
            return Credentials.from_authorized_user_file(self.token_file)
        return None
    
    def get_upcoming_events(self, max_results=5):
        creds = self.get_credentials()
        if not creds:
            return None
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            events = service.events().list(
                calendarId='primary',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events.get('items', [])
        except Exception as e:
            logger.error(f"Calendar error: {e}")
            return None

# === Smart Response Engine ===
class SmartResponseEngine:
    def __init__(self, user_id):
        self.user_id = user_id
        self.memory = EnhancedMemory(user_id)
        self.google = GoogleIntegration(user_id)
    
    def generate_response(self, message):
        # Personal info requests
        if any(x in message.lower() for x in ["איך קוראים לי", "השם שלי"]):
            name = self.memory.data["personal_details"].get("name")
            return f"קוראים לך {name} 😊" if name else "עדיין לא למדתי את שמך!"
        
        # Calendar requests
        if "מה בתכנית היום" in message.lower():
            events = self.google.get_upcoming_events()
            if events is None:
                return "צריך לאשר גישה ליומן Google תחילה 🔐"
            if not events:
                return "אין אירועים מתוכננים להיום 🎉"
            
            events_str = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if 'dateTime' in event['start']:
                    start_time = parse(start).strftime('%H:%M')
                    events_str.append(f"⏰ {event['summary']} ב-{start_time}")
                else:
                    events_str.append(f"📅 {event['summary']} (כל היום)")
            
            return "האירועים הקרובים:\n" + "\n".join(events_str)
        
        return None

# === Telegram Bot Handler ===
class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id: int, text: str):
        try:
            url = f"{self.api_url}/sendMessage"
            data = {"chat_id": chat_id, "text": text[:4096]}
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"ok": False}
    
    def process_update(self, update: Dict[str, Any]):
        try:
            if "message" not in update:
                logger.warning("Update does not contain message")
                return
            
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_id = str(message["from"]["id"])
            text = message.get("text", "")
            
            logger.info(f"Processing message from user {user_id}: {text[:50]}...")
            
            # Initialize services
            smart_engine = SmartResponseEngine(user_id)
            enhanced_memory = EnhancedMemory(user_id)
            
            # Process personal info
            enhanced_memory.extract_personal_info(text)
            
            # Generate response
            response = smart_engine.generate_response(text) or "אני עדיין לומדת לענות על שאלות כאלה! 🤖"
            
            self.send_message(chat_id, response)
            
        except Exception as e:
            logger.error(f"Failed to process update: {e}")

# === Flask Routes ===
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "service": "Maya Bot",
        "version": "4.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            update = request.get_json()
            if not update:
                logger.warning("Received empty webhook update")
                return jsonify({"status": "error", "message": "Empty request"}), 400
                
            bot.process_update(update)
            return jsonify({"status": "success"}), 200
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Method not allowed"}), 405

@app.route('/auth/google', methods=['POST'])
def google_auth():
    try:
        user_id = request.json.get("user_id")
        token_data = request.json.get("token")
        
        if not user_id or not token_data:
            return jsonify({"status": "error", "message": "Missing data"}), 400
        
        os.makedirs(config.SECURE_STORAGE_PATH, exist_ok=True)
        token_file = f"{config.SECURE_STORAGE_PATH}user_{user_id}_token.json"
        
        with open(token_file, "w") as f:
            json.dump(token_data, f)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        return jsonify({"status": "error"}), 500

# === Initialization ===
bot = TelegramBot()

# === Request Logging ===
@app.before_request
def log_request():
    logger.info(f"Incoming {request.method} request to {request.path}")

# === Error Handlers ===
@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', config.PORT))
    
    if config.ENVIRONMENT == 'production':
        from gunicorn.app.base import BaseApplication
        
        class FlaskApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.application = app
                self.options = options or {}
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key, value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 2,
            'timeout': 120,
            'worker_class': 'sync'
        }
        
        FlaskApplication(app, options).run()
    else:
        app.run(host='0.0.0.0', port=port, debug=config.DEBUG)