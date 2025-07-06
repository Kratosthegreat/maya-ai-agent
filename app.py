import os
import json
import re
import time
import logging
from datetime import datetime
import requests
import pytz
import random

from flask import Flask, request, jsonify

# Simple config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 10000))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple Maya Bot
class MayaBot:
    def __init__(self):
        self.user_names = {}
        self.responses = {
            "greetings": [
                "שלום! אני מאיה 😊 איך אוכל לעזור לך?",
                "היי! שמחה לפגוש אותך! במה אוכל לסייע?",
                "שלום וברכה! אני כאן לעזור לך עם כל שאלה."
            ],
            "time": [
                "השעה עכשיו: {time}",
                "🕐 השעה בישראל: {time}",
                "הזמן הנוכחי: {time}"
            ],
            "thanks": [
                "😊 בכיף! תמיד נעים לעזור",
                "🙏 בבקשה! אני כאן בשבילך",
                "❤️ שמחה שיכולתי לעזור!"
            ],
            "unknown": [
                "🤔 מעניין! תוכל לספר לי עוד על זה?",
                "לא בטוחה שהבנתי. תוכל לנסח אחרת?",
                "זה נושא מעניין! איך אוכל לעזור בדיוק?"
            ],
            "casual": [
                "מה שלומך? שמחה לשמוע ממך! 😊",
                "הכל בסדר! איך אתה מרגיש היום?",
                "טוב מאוד! מה המצב אצלך?"
            ]
        }
    
    def get_current_time(self):
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        return now.strftime("%H:%M - %d/%m/%Y")
    
    def process_message(self, user_id, message):
        message_lower = message.lower().strip()
        
        # Handle name
        name_patterns = [
            r"שמי (.+)", r"קוראים לי (.+)", r"השם שלי (.+)", r"אני (.+)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                if len(name) < 20:
                    self.user_names[user_id] = name
                    return f"נעים להכיר, {name}! 😊 איך אוכל לעזור לך?"
        
        # Get user name
        user_name = self.user_names.get(user_id, "")
        name_suffix = f" {user_name}" if user_name else ""
        
        # Greetings
        if any(word in message_lower for word in ["שלום", "היי", "הי", "בוקר טוב", "ערב טוב"]):
            response = random.choice(self.responses["greetings"])
            if name_suffix:
                response = response.replace("!", f"{name_suffix}!")
            return response
        
        # Time
        if any(word in message_lower for word in ["שעה", "זמן", "תאריך", "יום"]):
            current_time = self.get_current_time()
            return random.choice(self.responses["time"]).format(time=current_time)
        
        # Thanks
        if any(word in message_lower for word in ["תודה", "מעריך", "אסיר תודה"]):
            return random.choice(self.responses["thanks"])
        
        # Status questions
        if any(phrase in message_lower for phrase in ["מה שלומך", "איך אתה", "מה המצב", "איך הולך"]):
            return random.choice(self.responses["casual"])
        
        # Confused responses
        if any(word in message_lower for word in ["לא הגיון", "מבולבל", "מה את", "???", "!!!"]):
            confused_responses = [
                "סליחה אם בלבלתי אותך! 😅 בוא ננסה שוב - במה אוכל לעזור?",
                "אופס! נראה שלא הבנתי טוב. תוכל להסביר מה אתה מחפש?",
                "מצטערת על הבלבול! 😊 איך אוכל לעזור לך טוב יותר?"
            ]
            return random.choice(confused_responses)
        
        # Help requests
        if any(word in message_lower for word in ["עזור", "עזרה", "אוכל", "תוכל", "בעיה"]):
            help_responses = [
                f"בוודאי{name_suffix}! במה בדיוק אוכל לעזור לך?",
                "אני כאן לעזור! תגיד לי מה אתה צריך.",
                "אשמח לסייע! איך אוכל לעזור לך?"
            ]
            return random.choice(help_responses)
        
        # Default
        return random.choice(self.responses["unknown"])

# Bot instance
maya = MayaBot()

# Telegram functions
def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False

# Routes
@app.route("/")
def home():
    return jsonify({
        "status": "Maya Bot Working! 🤖",
        "version": "Simple 1.0",
        "time": maya.get_current_time(),
        "users": len(maya.user_names)
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        if not update or "message" not in update:
            return "OK"
        
        message = update["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")
        
        if chat_id and text and user_id:
            logger.info(f"Message from {user_id}: {text[:30]}...")
            response = maya.process_message(user_id, text)
            send_message(chat_id, response)
        
        return "OK"
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ERROR"

@app.route("/test")
def test():
    return jsonify({
        "test_message": "Maya is working!",
        "sample_responses": {
            "היי": maya.process_message(123, "היי"),
            "מה השעה": maya.process_message(123, "מה השעה"),
            "שמי דוד": maya.process_message(123, "שמי דוד")
        }
    })

if __name__ == "__main__":
    logger.info("🚀 Starting Simple Maya Bot")
    app.run(host="0.0.0.0", port=PORT, debug=False)
