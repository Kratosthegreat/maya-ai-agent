import os
import re
import logging
from datetime import datetime
import requests
import pytz
from flask import Flask, request, jsonify

# Config - Load from environment with validation
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN in environment variables")

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
if not HUGGINGFACE_API_KEY:
    raise ValueError("Missing HUGGINGFACE_API_KEY in environment variables")

PORT = int(os.getenv("PORT", 10000))
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")
if not WEBHOOK_SECRET_TOKEN:
    logging.warning("Running without WEBHOOK_SECRET_TOKEN - not recommended for production")

# Constants - HuggingFace API
HF_API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
MAX_HISTORY_LENGTH = 10
REQUEST_TIMEOUT = 30

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaBot:
    def __init__(self):
        self.user_names = {}
        self.conversation_history = {}
        self.rate_limits = {}

    def get_israel_time(self):
        """Get current Israeli time with Hebrew day names"""
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        
        hebrew_days = {
            'Monday': 'שני', 'Tuesday': 'שלישי', 'Wednesday': 'רביעי',
            'Thursday': 'חמישי', 'Friday': 'שישי', 'Saturday': 'שבת', 'Sunday': 'ראשון'
        }
        day_name = hebrew_days.get(now.strftime('%A'), now.strftime('%A'))
        
        return {
            'time': now.strftime('%H:%M'),
            'date': now.strftime('%d/%m/%Y'),
            'day': day_name,
            'full': f"יום {day_name}, {now.strftime('%d/%m/%Y')} בשעה {now.strftime('%H:%M')}"
        }

    def _check_rate_limit(self, user_id):
        """Implement basic rate limiting (10 requests per minute)"""
        current_time = datetime.now().timestamp()
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Remove old requests (older than 1 minute)
        self.rate_limits[user_id] = [
            t for t in self.rate_limits[user_id] 
            if current_time - t < 60
        ]
        
        if len(self.rate_limits[user_id]) >= 10:
            return False
        
        self.rate_limits[user_id].append(current_time)
        return True

    def process_message(self, user_id, message):
        # Check rate limit first
        if not self._check_rate_limit(user_id):
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return "אני צריכה לנוח רגע, נדבר עוד דקה? 😴"

        text_lower = message.lower().strip()

        # 1. Handle name introduction
        name_patterns = [
            r'(?:שמי|קוראים לי|השם שלי) (?:הוא )?([א-ת\s]{2,15})(?:\s|$|\.)',
            r'אני ([א-ת\s]{2,15})(?:\s|$|\.)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 1 and len(name) < 15 and name not in ["הוא", "היא", "אתה", "את"]:
                    self.user_names[user_id] = name
                    self._add_to_history(user_id, "user", message)
                    response_text = f"נעים מאוד להכיר אותך, {name}! 😊 אני מאיה, העוזרת הדיגיטלית שלך."
                    self._add_to_history(user_id, "assistant", response_text)
                    return response_text

        # 2. Handle TIME/DATE questions (local processing - no API needed)
        time_phrases = [
            'מה השעה', 'איזה יום', 'מה התאריך', 'תאריך היום', 
            'איזה תאריך', 'כמה השעה', 'מה הזמן', 'זמן עכשיו'
        ]
        if any(phrase in text_lower for phrase in time_phrases):
            time_info = self.get_israel_time()
            self._add_to_history(user_id, "user", message)
            response_text = f"🕐 {time_info['full']}"
            self._add_to_history(user_id, "assistant", response_text)
            return response_text

        # Prepare for HuggingFace API call
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
        }

        # Simple payload for text generation
        payload = {
            "inputs": f"משתמש: {message}\nמאיה:",
            "parameters": {
                "max_new_tokens": 50,
                "temperature": 0.7,
                "do_sample": True
            }
        }

        try:
            logger.info(f"🤗 Sending request to HuggingFace API: {HF_API_URL}")
            logger.info(f"📝 Input: {message[:40]}...")
            
            response = requests.post(
                HF_API_URL,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            logger.info(f"📊 HuggingFace response status: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"HuggingFace API error: {response.status_code} - {response.text[:300]}"
                logger.error(error_msg)
                
                # Return appropriate fallback based on error type
                if response.status_code == 401:
                    return "יש בעיה עם המפתח שלי 🔑"
                elif response.status_code == 429:
                    return "יותר מדי בקשות, נסה בעוד דקה ⏳"
                elif response.status_code == 503:
                    return "השירות עמוס, נסה בעוד דקה 🔄"
                else:
                    return "משהו השתבש, בוא ננסה שוב! ✨"

            response_json = response.json()
            logger.info(f"✅ HuggingFace response success!")
            
            # Handle different response formats
            if isinstance(response_json, list) and len(response_json) > 0:
                if "generated_text" in response_json[0]:
                    reply = response_json[0]["generated_text"]
                    # Extract only the assistant's response
                    if "מאיה:" in reply:
                        reply = reply.split("מאיה:")[-1].strip()
                else:
                    reply = str(response_json[0])
            else:
                logger.error("❌ Unexpected response format from HuggingFace")
                return "לא קיבלתי תשובה טובה, תנסה שוב! 🤔"

            cleaned_reply = self._clean_llm_response(reply)

            # Update conversation history
            self._add_to_history(user_id, "user", message)
            self._add_to_history(user_id, "assistant", cleaned_reply)

            logger.info(f"🎉 Success! Reply: {cleaned_reply}")
            return cleaned_reply

        except requests.exceptions.Timeout:
            logger.error("⏰ HuggingFace API timeout")
            return "לוקח לי יותר מדי זמן לחשוב, נסה שוב! ⏳"
        except requests.exceptions.RequestException as e:
            logger.error(f"🔌 HuggingFace API connection error: {e}")
            return "יש לי בעיה להתחבר, נסה שוב בעוד דקה! 🔌"
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            return "משהו השתבש, אבל אני כבר מטפלת בזה! 🛠️"

    def _add_to_history(self, user_id, role, content):
        """Manage conversation history with size limit"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({"role": role, "content": content})
        
        if len(self.conversation_history[user_id]) > MAX_HISTORY_LENGTH:
            self.conversation_history[user_id] = self.conversation_history[user_id][-MAX_HISTORY_LENGTH:]

    def _clean_llm_response(self, response_text: str) -> str:
        """Enforce Maya's personality rules in responses"""
        if isinstance(response_text, bytes):
            response_text = response_text.decode('utf-8')
        
        # Remove forbidden phrases
        forbidden_phrases = [
            r'\bאני מצטערת\b', r'\bאני חושבת\b', r'\bייתכן ש\b', r'\bאני לא בטוחה\b',
            r'\bכמודל שפה גדול\b', r'\bאני אשתדל\b', r'\bלפי המידע שלי\b', r'\bהאם אני יכולה לעזור\b',
            r'\bמה השם היפה שלך\b', r'\bכיף לדבר איתך\b', r'\bשמעו\b', r'\bברור!\b'
        ]
        for phrase_regex in forbidden_phrases:
            response_text = re.sub(phrase_regex, "", response_text, flags=re.IGNORECASE).strip()

        # Clean formatting and punctuation
        response_text = re.sub(r'```.*?```', '', response_text, flags=re.DOTALL)
        response_text = re.sub(r'[*_`]', '', response_text)
        response_text = " ".join(response_text.split())
        response_text = re.sub(r'^[.,;!?-]+', '', response_text).strip()
        response_text = re.sub(r'[.,;!?-]+$', '', response_text).strip()

        # If response is empty or too short, provide fallback
        words = response_text.split()
        if not words or len(response_text) < 3:
            return "היי! איך אני יכולה לעזור? 😊"
        
        # Enforce length limit
        if len(words) > 10:
            response_text = " ".join(words[:10])

        # Select appropriate emoji
        text_lower = response_text.lower()
        if any(w in text_lower for w in ["נעים", "כיף", "טוב", "שמחה"]):
            emoji = "😊"
        elif any(w in text_lower for w in ["תודה", "בכיף"]):
            emoji = "✨"
        elif any(w in text_lower for w in ["זמן", "שעה", "תאריך"]):
            emoji = "🕐"
        elif any(w in text_lower for w in ["עזרה", "לעזור"]):
            emoji = "💪"
        elif any(w in text_lower for w in ["לא מבין", "???", "!!!"]):
            emoji = "🤔"
        elif any(w in text_lower for w in ["תקוע", "עייף", "מתוסכל"]):
            emoji = "🫂"
        else:
            emoji = "👍"

        return f"{response_text} {emoji}".strip()

# Initialize bot
maya = MayaBot()

def send_message(chat_id, text):
    """Send message through Telegram API with retry logic"""
    try:
        response = requests.post(
            TELEGRAM_API_URL,
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"Telegram API error: {response.status_code} - {response.text}")
            return False
            
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram send error: {e}")
        return False

@app.route("/")
def home():
    time_info = maya.get_israel_time()
    return jsonify({
        "status": "🤗 Maya Bot - Powered by HuggingFace (FREE!)",
        "current_time": time_info['full'],
        "active_users": len(maya.conversation_history),
        "model": "microsoft/DialoGPT-medium",
        "api": "HuggingFace",
        "version": "3.0.0"
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    # Verify secret token if configured
    if WEBHOOK_SECRET_TOKEN:
        header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not header_secret or header_secret != WEBHOOK_SECRET_TOKEN:
            logger.warning("Unauthorized webhook access attempt")
            return "Unauthorized", 403
    
    try:
        update = request.get_json()
        if not update or "message" not in update:
            return "OK"

        message = update["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")

        if chat_id and text and user_id:
            logger.info(f"Processing message from {user_id}: {text[:40]}...")
            response = maya.process_message(user_id, text)
            logger.info(f"Sending response: {response[:40]}...")
            send_message(chat_id, response)
        
        return "OK"

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return "ERROR", 500

@app.route("/test")
def test():
    test_user_id = 999999999
    maya.conversation_history.pop(test_user_id, None)
    maya.user_names.pop(test_user_id, None)

    test_cases = [
        ("שלום מאיה!", "greeting"),
        ("קוראים לי דנה", "name introduction"),
        ("מה השעה?", "time query"),
        ("איך אתה מרגיש היום?", "emotional check")
    ]

    results = {}
    for text, description in test_cases:
        results[description] = maya.process_message(test_user_id, text)

    return jsonify({
        "status": "Test completed with HuggingFace",
        "api": "HuggingFace",
        "model": "microsoft/DialoGPT-medium",
        "results": results
    })

if __name__ == "__main__":
    logger.info("🚀 Maya Bot is running with HuggingFace API - FREE & SIMPLE!")
    app.run(host="0.0.0.0", port=PORT, debug=False)
