# -*- coding: utf-8 -*-
# === Maya Secretary Bot 5.1 - Fixed Response Version ===
import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dateutil.parser import parse

# === Configuration ===
class Config:
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
        if not self.TELEGRAM_TOKEN:
            raise ValueError("Missing TELEGRAM_TOKEN environment variable")
        
        self.PORT = int(os.getenv('PORT', 10000))  # Using port 10000 as detected
        self.DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
        self.WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')

config = Config()

# === Logging ===
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# === Enhanced Telegram Bot Handler ===
class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.user_sessions = {}  # Simple session storage
    
    def send_message(self, chat_id: int, text: str) -> bool:
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                },
                timeout=5
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        text = message.get("text", "").strip()
        user_id = message["from"]["id"]
        
        # Initialize session if new user
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                "first_seen": datetime.now(),
                "message_count": 0
            }
        
        self.user_sessions[user_id]["message_count"] += 1
        
        # Handle /start command
        if text.lower() == "/start":
            return "👋 שלום! אני מאיה, העוזרת האישית שלך. איך אוכל לעזור לך היום?"
        
        # Handle basic greetings
        if any(word in text.lower() for word in ["היי", "שלום", "הייי"]):
            return "👋 היי! נעים להכיר. מה שלומך היום?"
        
        # Handle "Maya" mentions
        if "מאיה" in text:
            return "כן? אני כאן! איך אוכל לעזור לך?"
        
        # Default response for unrecognized messages
        return "אני עדיין לומדת להכיר אותך! תוכל לשאול אותי שאלות פשוטות או להגיד 'מה אתה יודעת לעשות?'"

    def process_update(self, update: Dict[str, Any]):
        if "message" not in update:
            return
        
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        
        logger.info(f"Processing message from user {user_id}: {message.get('text', '')[:50]}...")
        
        # Generate response
        response = self.process_message(message)
        if response:
            self.send_message(chat_id, response)

# === Flask Routes ===
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "service": "Maya Bot",
        "version": "5.1",
        "port": config.PORT,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
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

# === Initialization ===
bot = TelegramBot()

if __name__ == '__main__':
    logger.info(f"Starting Maya Bot on port {config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT, debug=config.DEBUG)