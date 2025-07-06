import os
import re
import logging
from datetime import datetime
import requests
import pytz
import random
from flask import Flask, request, jsonify

# Config - Load from environment with validation
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN in environment variables")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("Missing OPENROUTER_API_KEY in environment variables")

PORT = int(os.getenv("PORT", 10000))
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")
if not WEBHOOK_SECRET_TOKEN:
    logging.warning("Running without WEBHOOK_SECRET_TOKEN - not recommended for production")

# Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
MAX_HISTORY_LENGTH = 10  # Keep last 5 conversation turns (user + assistant)
REQUEST_TIMEOUT = 30  # seconds - increased from 20

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaBot:
    def __init__(self):
        self.user_names = {}
        self.conversation_history = {}
        self.rate_limits = {}  # Track user request timestamps for rate limiting

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
        """Implement basic rate limiting (5 requests per minute)"""
        current_time = datetime.now().timestamp()
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Remove old requests (older than 1 minute)
        self.rate_limits[user_id] = [
            t for t in self.rate_limits[user_id] 
            if current_time - t < 60
        ]
        
        if len(self.rate_limits[user_id]) >= 5:
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

        # דיאגנוסטיקה - בדיקת מודלים זמינים
        if text_lower in ["דיאגנוסטיקה", "בדיקה", "טסט", "test"]:
            return self._run_model_diagnosis()

        # Prepare for API call
        user_name = self.user_names.get(user_id, "")
        name_suffix = f" {user_name}" if user_name else ""

        system_prompt = f"""
        את מאיה, המזכירה האישית של{name_suffix}. את חכמה, רגישה, מבינה רמזים רגשיים, ומדברת בעברית בלבד.
        את לא רובוט – את מגיבה כמו אדם חם, נעים, מצחיק לפעמים, או מרגיעה כשצריך.
        תמיד תהיי בטוחה במה שאת אומרת.
        אם המשתמש שואל שאלה פשוטה – תעני ישר ולעניין.
        אם הוא מרגיש תקוע, עייף או מתוסכל – תגיבי בהתאם ברגישות.
        תמיד תעני בקצרה, בין 1-10 מילים.
        תמיד תסיימי את התשובה באימוג'י אחד בלבד, שמתאים לתשובה.
        אסור לך להשתמש בביטויים כמו "אני מצטערת", "אני חושבת", "ייתכן ש", "אני לא בטוחה", "כמודל שפה גדול".
        """

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if user_id in self.conversation_history:
            messages.extend(self.conversation_history[user_id])
        
        # Add current message
        messages.append({"role": "user", "content": message})

        # רשימת מודלים לנסות (בסדר עדיפות)
        models_to_try = [
            "microsoft/wizardlm-2-8x22b:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "google/gemma-7b-it:free",
            "huggingfaceh4/zephyr-7b-beta:free"
        ]

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://maya-bot.onrender.com",
            "X-Title": "Maya Bot"
        }

        last_error = None
        
        # נסה כל מודל עד שאחד עובד
        for model_name in models_to_try:
            data = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150
            }

            try:
                logger.info(f"🔄 מנסה מודל: {model_name}")
                logger.info(f"Sending request to OpenRouter API: {OPENROUTER_API_URL}")
                
                response = requests.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=data,
                    timeout=REQUEST_TIMEOUT
                )

                logger.info(f"📊 סטטוס מודל {model_name}: {response.status_code}")
                
                if response.status_code == 200:
                    response_json = response.json()
                    logger.info(f"✅ מודל {model_name} עבד! תשובה: {response_json}")
                    
                    if "choices" in response_json and response_json["choices"]:
                        reply = response_json["choices"][0]["message"]["content"]
                        cleaned_reply = self._clean_llm_response(reply)

                        # Update conversation history
                        self._add_to_history(user_id, "user", message)
                        self._add_to_history(user_id, "assistant", cleaned_reply)

                        logger.info(f"🎉 השתמשתי במודל: {model_name}")
                        return cleaned_reply
                
                # אם הגענו לכאן, המודל לא עבד
                error_details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                logger.warning(f"❌ מודל {model_name} נכשל: {error_details}")
                last_error = error_details
                
                # אם זה 401/403 - אין טעם לנסות מודלים אחרים
                if response.status_code in [401, 403]:
                    logger.error("🔑 בעיית הרשאה - עוצר ניסיונות נוספים")
                    break
                    
            except requests.exceptions.Timeout:
                logger.error(f"⏰ Timeout למודל {model_name}")
                last_error = "Timeout"
                continue
            except requests.exceptions.RequestException as e:
                logger.error(f"🔌 בעיית חיבור למודל {model_name}: {e}")
                last_error = str(e)
                continue
            except Exception as e:
                logger.error(f"💥 שגיאה כללית למודל {model_name}: {e}")
                last_error = str(e)
                continue

        # אם כל המודלים נכשלו
        logger.error(f"💀 כל המודלים נכשלו! שגיאה אחרונה: {last_error}")
        
        # תן הודעת שגיאה מידעת יותר
        if "401" in str(last_error) or "403" in str(last_error):
            return "יש בעיה עם המפתח שלי 🔑"
        elif "404" in str(last_error):
            return "המודלים לא זמינים כרגע 🚫"
        elif "429" in str(last_error):
            return "יותר מדי בקשות, נסה בעוד דקה ⏳"
        elif "timeout" in str(last_error).lower():
            return "לוקח יותר מדי זמן, נסה שוב ⏰"
        else:
            return "יש לי בעיה טכנית זמנית 🛠️"

    def _run_model_diagnosis(self):
        """רץ דיאגנוסטיקה מהירה של מודלים"""
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # בדוק אם יש גישה לרשימת מודלים
            models_response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=5)
            
            if models_response.status_code == 200:
                models_data = models_response.json()
                free_models = [m["id"] for m in models_data.get("data", []) if ":free" in m["id"]]
                return f"יש {len(free_models)} מודלים חינמיים זמינים ✅"
            else:
                return f"בעיה בגישה למודלים: {models_response.status_code} ❌"
                
        except Exception as e:
            return f"שגיאה בדיאגנוסטיקה: {str(e)[:50]} 🔧"

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

        # Enforce length and add emoji
        words = response_text.split()
        if not words:
            return "אני לא מבינה. 😕"
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
        "status": "🤖 Maya Bot - GPT via OpenRouter",
        "current_time": time_info['full'],
        "active_users": len(maya.conversation_history),
        "version": "1.1.0"
    })

@app.route("/deep-diagnosis")
def deep_diagnosis():
    """מערכת דיאגנוסטיקה מעמיקה לבעיות OpenRouter"""
    diagnosis_results = {}
    
    # בדיקה 1: חיבור בסיסי ל-OpenRouter
    try:
        test_url = "https://openrouter.ai/api/v1/models"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        models_response = requests.get(test_url, headers=headers, timeout=10)
        diagnosis_results["models_api_status"] = models_response.status_code
        diagnosis_results["models_api_response"] = models_response.text[:500] + "..." if len(models_response.text) > 500 else models_response.text
        
        if models_response.status_code == 200:
            models_data = models_response.json()
            available_models = [model["id"] for model in models_data.get("data", [])]
            free_models = [model for model in available_models if ":free" in model]
            diagnosis_results["total_models_available"] = len(available_models)
            diagnosis_results["free_models_count"] = len(free_models)
            diagnosis_results["free_models_sample"] = free_models[:10]  # ראשונים 10
            
            # בדיקה אם הדגמים שניסינו זמינים
            test_models = [
                "openai/gpt-3.5-turbo",
                "meta-llama/llama-3.1-8b-instruct:free", 
                "microsoft/wizardlm-2-8x22b:free",
                "mistralai/mistral-7b-instruct:free"
            ]
            for model in test_models:
                diagnosis_results[f"model_{model.replace('/', '_').replace(':', '_')}_available"] = model in available_models
        
    except Exception as e:
        diagnosis_results["models_api_error"] = str(e)
    
    # בדיקה 2: בדיקת API Key עם completion פשוט
    free_models_to_test = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "microsoft/wizardlm-2-8x22b:free", 
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-7b-it:free",
        "huggingfaceh4/zephyr-7b-beta:free"
    ]
    
    for model_name in free_models_to_test:
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://maya-bot.onrender.com",
                "X-Title": "Maya Bot Diagnosis"
            }
            
            data = {
                "model": model_name,
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0.7,
                "max_tokens": 10
            }
            
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=15)
            
            diagnosis_results[f"test_{model_name.replace('/', '_').replace(':', '_')}"] = {
                "status_code": response.status_code,
                "response_preview": response.text[:200] + "..." if len(response.text) > 200 else response.text,
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                diagnosis_results["WORKING_MODEL_FOUND"] = model_name
                break
                
        except Exception as e:
            diagnosis_results[f"test_{model_name.replace('/', '_').replace(':', '_')}_error"] = str(e)
    
    # בדיקה 3: בדיקת חשבון וקרדיטים
    try:
        credits_url = "https://openrouter.ai/api/v1/auth/key"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        credits_response = requests.get(credits_url, headers=headers, timeout=10)
        
        diagnosis_results["account_status"] = credits_response.status_code
        if credits_response.status_code == 200:
            account_data = credits_response.json()
            diagnosis_results["account_info"] = account_data
        else:
            diagnosis_results["account_error"] = credits_response.text
            
    except Exception as e:
        diagnosis_results["account_check_error"] = str(e)
    
    # בדיקה 4: תוקף API Key
    api_key_valid = OPENROUTER_API_KEY and len(OPENROUTER_API_KEY) > 20 and OPENROUTER_API_KEY.startswith("sk-")
    diagnosis_results["api_key_format_valid"] = api_key_valid
    diagnosis_results["api_key_length"] = len(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else 0
    diagnosis_results["api_key_prefix"] = OPENROUTER_API_KEY[:10] + "..." if OPENROUTER_API_KEY else "None"
    
    # סיכום והמלצות
    recommendations = []
    if not api_key_valid:
        recommendations.append("🔑 API Key לא תקף - צריך להתחיל ב-sk- ולהיות ארוך יותר")
    
    if diagnosis_results.get("models_api_status") != 200:
        recommendations.append("🚫 לא מצליח לגשת לרשימת הדגמים - בדוק API Key")
    
    if diagnosis_results.get("free_models_count", 0) == 0:
        recommendations.append("💸 אין דגמים חינמיים זמינים - אולי צריך לקנות קרדיטים")
    
    if "WORKING_MODEL_FOUND" not in diagnosis_results:
        recommendations.append("❌ אף דגם לא עובד - בעיה בחשבון או במפתח")
    
    diagnosis_results["recommendations"] = recommendations
    diagnosis_results["timestamp"] = datetime.now().isoformat()
    
    return jsonify(diagnosis_results)

@app.route("/test-model")
def test_model():
    """Test OpenRouter API connection and model availability"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://maya-bot.onrender.com",
        "X-Title": "Maya Bot"
    }

    data = {
        "model": "microsoft/wizardlm-2-8x22b:free",
        "messages": [{"role": "user", "content": "Test message"}],
        "temperature": 0.7,
        "max_tokens": 50
    }

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=data,
            timeout=10
        )
        
        return jsonify({
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text,
            "headers": dict(response.headers),
            "api_url": OPENROUTER_API_URL,
            "model": data["model"]
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "api_url": OPENROUTER_API_URL,
            "model": data["model"]
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
        ("אני מרגיש עצוב היום", "emotional support"),
        ("תסבירי על בינה מלאכותית", "knowledge query"),
        ("לא הבנתי כלום", "confusion"),
        ("תודה רבה", "thanks")
    ]

    results = {}
    for text, description in test_cases:
        results[description] = maya.process_message(test_user_id, text)

    return jsonify({
        "status": "Test completed",
        "results": results
    })

if __name__ == "__main__":
    logger.info("🚀 Maya Bot is running with enhanced stability and error handling")
    app.run(host="0.0.0.0", port=PORT, debug=False)
