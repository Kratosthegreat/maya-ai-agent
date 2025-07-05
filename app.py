# -*- coding: utf-8 -*-
# === Maya Secretary Bot 4.0 - The PERSONAL Secretary Upgrade ===
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

# Config handling (unchanged)
try:
    from config import config
except ImportError:
    class Config:
        TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
        WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "YOUR_WEBHOOK_URL")
        PORT = int(os.environ.get("PORT", 5000))
        DEBUG = os.environ.get("DEBUG", "False").lower() in ('true', '1', 't')
        ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
        MAX_REQUESTS_PER_MINUTE = 20
        GEMINI_MODEL = "gemini-1.5-flash"
        SECURE_STORAGE_PATH = "secure_tokens/"
    config = Config()
    logging.warning("config.py not found. Using dummy config.")

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
            logging.error(f"Memory load error: {e}")
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
            logging.error(f"Memory save error: {e}")
    
    def extract_personal_info(self, text):
        text_lower = text.lower()
        # Name detection
        name_patterns = [r"קוראים לי (.+)", r"שמי (.+)", r"השם שלי (.+)"]
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match and len(match.group(1).split()) < 4:  # Avoid long false matches
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
            events_result = service.events().list(
                calendarId='primary',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            logging.error(f"Calendar error: {e}")
            return None

# === Smart Response Engine ===
class SmartResponseEngine:
    def __init__(self, user_id):
        self.user_id = user_id
        self.memory = EnhancedMemory(user_id)
        self.google = GoogleIntegration(user_id)
    
    def generate_response(self, message):
        # Check for personal info requests
        if any(x in message.lower() for x in ["איך קוראים לי", "השם שלי"]):
            name = self.memory.data["personal_details"].get("name")
            return f"קוראים לך {name} 😊" if name else "עדיין לא למדתי את שמך!"
        
        # Check calendar requests
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

# === (Keep all existing classes: WebSearchService, SuperWeatherService, etc.) ===
# [All your existing classes remain unchanged until the TelegramBot class]

class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id: int, text: str):
        # [Keep existing implementation]
        pass
    
    def process_update(self, update: Dict[str, Any]):
        # [Keep existing security checks]
        
        user_id = str(update["message"]["from"]["id"])
        text = update["message"].get("text", "")
        
        # Initialize enhanced services
        smart_engine = SmartResponseEngine(user_id)
        enhanced_memory = EnhancedMemory(user_id)
        
        # Extract personal info
        enhanced_memory.extract_personal_info(text)
        
        # Try smart response first
        response = smart_engine.generate_response(text)
        if not response:
            # Fallback to original AI
            response = ai_service.generate_response(user_id, text)
        
        self.send_message(update["message"]["chat"]["id"], response)

# === New Flask Routes ===
app = Flask(__name__)

@app.route("/auth/google", methods=["POST"])
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
        
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Google auth error: {e}")
        return jsonify({"status": "error"}), 500

# [Keep all existing routes: /webhook, /test_weather, etc.]

if __name__ == "__main__":
    # Initialize services
    security = SecurityService()
    user_service = UserService()
    weather_service = SuperWeatherService()
    ai_service = MayaAIService()
    bot = TelegramBot()
    
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)