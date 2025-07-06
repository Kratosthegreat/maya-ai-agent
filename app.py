import os
import re
import logging
from datetime import datetime
import requests
import pytz
import random # נשאר בשביל גמישות עתידית או אם יש רנדומליות אחרת

from flask import Flask, request, jsonify

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.getenv("PORT", 10000))
# מומלץ מאוד להגדיר את זה ב-Render/היכן שהקוד מאוחסן!
# לדוגמה: WEBHOOK_SECRET_TOKEN="my-super-secret-telegram-token-123"
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN") 

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaBot:
    def __init__(self):
        self.user_names = {}
        # New: Store conversation history for each user. In this setup, it's effectively for one user.
        self.conversation_history = {} 

    def get_israel_time(self):
        """Get current Israeli time"""
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        
        # Hebrew day names
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

    def process_message(self, user_id, message):
        text_lower = message.lower().strip()

        # 1. Handle name introduction FIRST
        # Added character range validation to regex and explicit check for Hebrew letters
        name_patterns = [
            r'(?:שמי|קוראים לי|השם שלי) (?:הוא )?([א-ת\s]{2,15})(?:\s|$|\.)', # More specific Hebrew name pattern
            r'אני ([א-ת\s]{2,15})(?:\s|$|\.)' # Also more specific
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                # Additional validation: name should not be a common Hebrew verb/preposition
                if name and len(name) > 1 and len(name) < 15 and name not in ["הוא", "היא", "אתה", "את", "אנחנו", "אתם", "הם"]:
                    self.user_names[user_id] = name
                    # Add to history
                    self._add_to_history(user_id, "user", message)
                    response_text = f"נעים מאוד להכיר אותך, {name}! 😊 אני מאיה, העוזרת הדיגיטלית שלך."
                    self._add_to_history(user_id, "assistant", response_text)
                    return response_text

        # 2. Handle TIME/DATE questions SPECIFICALLY (Re-integrated for accuracy and efficiency)
        if any(phrase in text_lower for phrase in [
            'מה השעה', 'איזה יום', 'מה התאריך', 'תאריך היום', 
            'איזה תאריך', 'כמה השעה', 'מה הזמן', 'זמן עכשיו'
        ]):
            time_info = self.get_israel_time()
            self._add_to_history(user_id, "user", message) # Add user message to history
            response_text = f"🕐 {time_info['full']}"
            self._add_to_history(user_id, "assistant", response_text) # Add bot response to history
            return response_text

        # Get user name for prompt and suffix
        user_name = self.user_names.get(user_id, "")
        name_suffix = f" {user_name}" if user_name else ""

        # Construct system prompt with personalized name and strict persona rules
        system_prompt = f"""
        את מאיה, המזכירה האישית של{name_suffix}. את חכמה, רגישה, מבינה רמזים רגשיים, ומדברת בעברית בלבד.
        את לא רובוט – את מגיבה כמו אדם חם, נעים, מצחיק לפעמים, או מרגיעה כשצריך.
        תמיד תהיי בטוחה במה שאת אומרת.
        אם המשתמש שואל שאלה פשוטה – תעני ישר ולעניין.
        אם הוא מרגיש תקוע, עייף או מתוסכל – תגיבי בהתאם ברגישות.
        תמיד תעני בקצרה, בין 1-10 מילים.
        תמיד תסיימי את התשובה באימוג'י אחד בלבד, שמתאים לתשובה.
        אסור לך להשתמש בביטויים כמו "אני מצטערת", "אני חושבת", "ייתכן ש", "אני לא בטוחה", "כמודל שפה גדול", "אני אשתדל", "לפי המידע שלי", "האם אני יכולה לעזור", "מה השם היפה שלך", "כיף לדבר איתך", "שמעו", "ברור!", "אני זוכרת הכל", "תזכיר לי", "אופס, נראה לי שמשהו לא ברור.", "אוקיי, הבנתי.", "אני עוזרת לך", "אני כאן בשבילך", "בצורה טבעית יותר".
        אם את לא מבינה שאלה, תגידי שאת לא מבינה וצריכה הבהרה, בצורה בטוחה וקצרה.
        """

        # Prepare messages for OpenRouter API, including history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Load last few turns of conversation history (user + assistant)
        if user_id in self.conversation_history:
            messages.extend(self.conversation_history[user_id]) 
        
        # Add current user message
        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://maya-bot.onrender.com" # Replace with your actual deployed URL
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": messages
        }

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=15 # Increased timeout for LLM response
            )
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            reply = response.json()["choices"][0]["message"]["content"]
            
            # Clean and validate the response from LLM to enforce persona
            cleaned_reply = self._clean_llm_response(reply)

            # Add user message and assistant reply to history
            self._add_to_history(user_id, "user", message)
            self._add_to_history(user_id, "assistant", cleaned_reply)

            return cleaned_reply
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request error: {e}")
            return "משהו התפקשש לי, בוא ננסה שוב! ✨" # More personality-consistent fallback
        except Exception as e:
            logger.error(f"OpenRouter GPT unexpected error: {e}")
            return "קצר בתקשורת, תנסה שוב! ⚡" # More personality-consistent fallback

    def _add_to_history(self, user_id, role, content):
        """Adds a message to the user's conversation history, keeping it limited."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({"role": role, "content": content})
        
        # Keep history limited to prevent excessive token usage (e.g., last 10 messages = 5 turns)
        if len(self.conversation_history[user_id]) > 10: 
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]

    def _clean_llm_response(self, response_text: str) -> str:
        """Cleans LLM response to enforce Maya's personality rules."""
        # Convert to Hebrew string if it's not already (safety check)
        if isinstance(response_text, bytes):
            response_text = response_text.decode('utf-8')
        
        # Remove forbidden phrases (case-insensitive and word boundaries)
        forbidden_phrases = [
            r'\bאני מצטערת\b', r'\bאני חושבת\b', r'\bייתכן ש\b', r'\bאני לא בטוחה\b', 
            r'\bכמודל שפה גדול\b', r'\bאני אשתדל\b', r'\bלפי המידע שלי\b', r'\bהאם אני יכולה לעזור\b',
            r'\bמה השם היפה שלך\b', r'\bכיף לדבר איתך\b', r'\bשמעו\b', r'\bברור!\b', 
            r'\bאני זוכרת הכל\b', r'\bתזכיר לי\b', r'\bאופס, נראה לי שמשהו לא ברור\.\b', 
            r'\bאוקיי, הבנתי\.\b', r'\bאני עוזרת לך\b', r'\bאני כאן בשבילך\b', 
            r'\bבצורה טבעית יותר\b', r'\bשלום לך\b', r'\bהיי לך\b', r'\bבוקר טוב לך\b', 
            r'\bערב טוב לך\b', r'\bלילה טוב לך\b', r'\bבסדר גמור\b', r'\bהכל טוב\b', 
            r'\bמעולה\b', r'\bתודה ששאלת\b', r'\bמה שלומך\b', r'\bאיך אתה\b', r'\bאיך את\b', 
            r'\bמה המצב\b', r'\bאיך הולך\b', r'\bמעניין\b', r'\bלא בטוחה\b', r'\bזה נושא מעניין\b',
            r'\bאני עדיין לומדת\b', r'\bבכיף\b', r'\bבבקשה\b', r'\bשמחה שיכולתי לעזור\b',
            r'\bבוודאי\b', r'\bאני כאן לעזור\b', r'\bאשמח לסייע\b', r'\bאני מאיה\b',
            r'\bשמי מאיה\b', r'\bאני בוט חכם\b', r'\bהמזכירה הדיגיטלית שלך\b', r'\bמאיה העוזרת הדיגיטלית\b'
        ]
        for phrase_regex in forbidden_phrases:
            response_text = re.sub(phrase_regex, "", response_text, flags=re.IGNORECASE).strip()

        # Remove markdown characters (bold, italics, code blocks)
        response_text = re.sub(r'```.*?```', '', response_text, flags=re.DOTALL) # Code blocks
        response_text = re.sub(r'[*_`]', '', response_text) # Bold/italics/inline code

        # Clean multiple spaces and leading/trailing punctuation
        response_text = " ".join(response_text.split()) # Remove extra spaces
        response_text = re.sub(r'^[.,;!?-]+', '', response_text).strip() # Remove leading punctuation
        response_text = re.sub(r'[.,;!?-]+$', '', response_text).strip() # Remove trailing punctuation (before emoji)

        # Enforce max words (1-10 words)
        words = response_text.split()
        if len(words) == 0: # Handle empty string after cleaning
            return "אני לא מבינה. 😕" # Fallback if everything was removed
        if len(words) > 10:
            response_text = " ".join(words[:10])

        # Ensure exactly one emoji at the end
        # First, remove all existing emojis from the text part
        text_without_emojis = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U0001F900-\U0001F9FF]+', '', response_text).strip()
        
        # Determine appropriate emoji based on content (can be expanded)
        # Using a fixed mapping here, consider more advanced sentiment analysis for richer emoji selection
        if any(w in text_without_emojis for w in ["נעים", "כיף", "טוב", "שמחה", "מוכן", "מעולה"]):
            chosen_emoji = "😊"
        elif any(w in text_without_emojis for w in ["תודה", "בכיף"]):
            chosen_emoji = "✨"
        elif any(w in text_without_emojis for w in ["זמן", "שעה", "תאריך", "יום"]):
            chosen_emoji = "🕐"
        elif any(w in text_without_emojis for w in ["עזרה", "לעזור", "צריך", "אשמח"]):
            chosen_emoji = "💪"
        elif any(w in text_without_emojis for w in ["מבלבל", "לא מבין", "לנסח", "???", "!!!", "קצר"]):
            chosen_emoji = "🤔"
        elif any(w in text_without_emojis for w in ["תקוע", "עייף", "מתוסכל", "קשה"]):
            chosen_emoji = "🫂" # Hugging face for empathy
        else:
            chosen_emoji = "👍" # Default positive emoji

        final_response = f"{text_without_emojis} {chosen_emoji}".strip()
        return final_response


# Bot instance
maya = MayaBot()

def send_message(chat_id, text):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=data, timeout=5)
        # Log more details if sending fails
        if response.status_code != 200:
            logger.error(f"Telegram API error sending message: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False

@app.route("/")
def home():
    time_info = maya.get_israel_time()
    return jsonify({
        "status": "🤖 Maya Bot - GPT via OpenRouter",
        "current_time": time_info['full'],
        "users_with_names": len(maya.user_names), # Should ideally be 0 or 1 now
        "features": [
            "✅ GPT (3.5-turbo) עם עברית טבעית",
            "✅ הבנה רגשית והקשרית",
            "✅ שמירת שמות משתמשים (בזיכרון בלבד)",
            "✅ בוט רגיש וחם, לא רובוטי",
            "✅ זיכרון שיחה מוגבל (5 תורות)",
            "✅ טיפול מדויק בשעה ותאריך",
            "✅ סינון תגובות LLM לאכיפת אישיות"
        ]
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Verify webhook secret token (highly recommended for production)
        if WEBHOOK_SECRET_TOKEN:
            header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if not header_secret or header_secret != WEBHOOK_SECRET_TOKEN:
                logger.warning("Unauthorized webhook access attempt (missing or incorrect secret token).")
                return "Unauthorized", 403 # Return 403 Forbidden
        
        update = request.get_json()
        if not update or "message" not in update:
            return "OK" # Acknowledge updates without message (e.g., channel_post)

        message = update["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id") # Get the user's ID

        if chat_id and text and user_id:
            logger.info(f"Processing message from user {user_id}: {text[:40]}...")
            response = maya.process_message(user_id, text)
            logger.info(f"Sending response to user {user_id}: {response[:40]}...")
            send_message(chat_id, response)
        
        return "OK" # Always return OK to Telegram

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ERROR" # Return ERROR in case of unhandled exception

@app.route("/test")
def test():
    # Simulate a user ID for testing purposes
    test_user_id = 999999999 
    
    # Reset history for the test user to ensure consistent testing
    if test_user_id in maya.conversation_history:
        del maya.conversation_history[test_user_id]
    if test_user_id in maya.user_names:
        del maya.user_names[test_user_id]

    # Test cases for LLM interaction and specific functionalities
    test_results = {
        "1_initial_greeting": maya.process_message(test_user_id, "שלום מאיה!"),
        "2_name_intro": maya.process_message(test_user_id, "קוראים לי אלון"),
        "3_name_recall_and_greeting": maya.process_message(test_user_id, "היי מאיה! מה שלומך?"),
        "4_time_query": maya.process_message(test_user_id, "מה השעה עכשיו?"),
        "5_emotional_query": maya.process_message(test_user_id, "אני מרגיש תקוע היום"),
        "6_general_question": maya.process_message(test_user_id, "מה זה בינה מלאכותית?"),
        "7_confusion": maya.process_message(test_user_id, "לא הבנתי כלום!!!"),
        "8_thanks": maya.process_message(test_user_id, "תודה רבה לך"),
        "9_follow_up_on_ai": maya.process_message(test_user_id, "תסבירי לי עוד על זה"), # Test conversation history
        "10_invalid_name": maya.process_message(test_user_id + 1, "אני בטטה") # Test for new user, invalid name
    }
    return jsonify({
        "message": "Test responses for Maya:",
        "tests": test_results
    })

if __name__ == "__main__":
    logger.info("🚀 Maya Bot is running with GPT via OpenRouter (gpt-3.5-turbo)")
    app.run(host="0.0.0.0", port=PORT, debug=False)
