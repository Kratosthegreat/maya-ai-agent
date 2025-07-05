# -*- coding: utf-8 -*-
# === Maya Secretary Bot 5.2 - Enhanced Response Version ===
import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pytz

from flask import Flask, request, jsonify
import requests

# === Configuration ===
class Config:
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
        if not self.TELEGRAM_TOKEN:
            raise ValueError("Missing TELEGRAM_TOKEN environment variable")
        
        self.PORT = int(os.getenv('PORT', 10000))
        self.DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
        self.TIMEZONE = pytz.timezone('Asia/Jerusalem')

config = Config()

# === Logging ===
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# === User Memory System ===
class UserMemory:
    def __init__(self):
        self.user_data = {}  # In-memory storage (replace with DB in production)
    
    def remember_name(self, user_id: int, name: str):
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['name'] = name
        logger.info(f"Remembered name for user {user_id}: {name}")
    
    def get_name(self, user_id: int) -> Optional[str]:
        return self.user_data.get(user_id, {}).get('name')

memory = UserMemory()

# === Telegram Bot Handler ===
class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
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
        
        # Handle name declaration
        name_match = re.search(r'(שמי|קוראים לי|השם שלי) (.+)', text)
        if name_match:
            name = name_match.group(2)
            memory.remember_name(user_id, name)
            return f"נעים להכיר אותך, {name}! 😊"
        
        # Handle time requests
        if 'מה השעה' in text or 'שעה עכשיו' in text:
            now = datetime.now(config.TIMEZONE)
            return f"השעה עכשיו בישראל היא: {now.strftime('%H:%M')} 🕒"
        
        # Check if we know the user's name
        user_name = memory.get_name(user_id)
        
        # Handle /start command
        if text.lower() == "/start":
            greeting = f"👋 שלום! אני מאיה" 
            if user_name:
                greeting += f", {user_name}"
            return greeting + "! איך אוכל לעזור לך היום?"
        
        # Handle greetings
        if any(word in text.lower() for word in ["היי", "שלום", "הייי"]):
            greeting = "👋 היי"
            if user_name:
                greeting += f" {user_name}"
            return greeting + "! מה שלומך היום?"
        
        # Handle "Maya" mentions
        if "מאיה" in text:
            return "כן? אני כאן! איך אוכל לעזור לך?"
        
        # Default response
        return "אשמח לעזור! תוכל לשאול אותי על:\n- מה השעה עכשיו\n- לשמור את שמך\n- או כל בקשה אחרת"

    def process_update(self, update: Dict[str, Any]):
        if "message" not in update:
            return
        
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        
        logger.info(f"Processing message from user {user_id}: {message.get('text', '')}")
        
        # Generate and send response
        response = self.process_message(message)
        if response:
            success = self.send_message(chat_id, response)
            if not success:
                logger.error(f"Failed to send response to user {user_id}")

# === Flask Routes ===
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "service": "Maya Bot",
        "version": "5.2",
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