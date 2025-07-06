import os
import re
import time
import logging
from datetime import datetime
import requests
import pytz
import random

from flask import Flask, request, jsonify

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 10000))

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaBot:
    def __init__(self):
        self.user_names = {}
    
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
        """Process message with clear logic"""
        text = message.lower().strip()
        
        # 1. Handle name introduction FIRST
        name_patterns = [
            r'שמי (הוא )?(.+?)(?:\s|$|\.)',
            r'קוראים לי (.+?)(?:\s|$|\.)',
            r'השם שלי (הוא )?(.+?)(?:\s|$|\.)',
            r'אני (.+?)(?:\s|$|\.)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(-1).strip()
                if len(name) > 0 and len(name) < 15:
                    self.user_names[user_id] = name
                    return f"נעים מאוד להכיר אותך, {name}! 😊 אני מאיה, העוזרת הדיגיטלית שלך."
        
        # Get user name if we have it
        user_name = self.user_names.get(user_id, "")
        name_suffix = f" {user_name}" if user_name else ""
        
        # 2. Handle TIME/DATE questions SPECIFICALLY
        if any(phrase in text for phrase in [
            'מה השעה', 'איזה יום', 'מה התאריך', 'תאריך היום', 
            'איזה תאריך', 'כמה השעה', 'מה הזמן', 'זמן עכשיו'
        ]):
            time_info = self.get_israel_time()
            return f"🕐 {time_info['full']}"
        
        # 3. Handle GREETINGS
        if any(word in text for word in ['שלום', 'היי', 'הי', 'הייי', 'בוקר טוב', 'ערב טוב', 'לילה טוב']):
            greetings = [
                f"שלום{name_suffix}! 😊 איך אוכל לעזור לך היום?",
                f"היי{name_suffix}! 👋 מה שלומך? במה אוכל לסייע?",
                f"שלום{name_suffix}! שמחה לראות אותך! איך אוכל לעזור?"
            ]
            return random.choice(greetings)
        
        # 4. Handle STATUS questions
        if any(phrase in text for phrase in ['מה שלומך', 'איך אתה', 'איך את', 'מה המצב', 'איך הולך']):
            status_responses = [
                f"הכל טוב{name_suffix}! 😊 תודה ששאלת. איך אתה מרגיש?",
                f"מעולה{name_suffix}! 💪 אני כאן ומוכנה לעזור. מה איתך?",
                f"בסדר גמור{name_suffix}! 🙂 איך אוכל לעזור לך היום?"
            ]
            return random.choice(status_responses)
        
        # 5. Handle CONFUSION/COMPLAINTS
        if any(phrase in text for phrase in [
            'לא הגיון', 'מבלבל', 'לא מבין', 'מה את מדברת', 
            'לא קשור', 'שטויות', '???', '!!!'
        ]):
            confusion_responses = [
                "אופס! 😅 נראה שלא הבנתי טוב את השאלה. תוכל לנסח אותה אחרת?",
                "סליחה על הבלבול! 🤦‍♀️ בוא ננסה שוב - מה בדיוק אתה רוצה לדעת?",
                "מצטערת! 😊 לפעמים אני מתבלבלת. איך אוכל לעזור לך טוב יותר?"
            ]
            return random.choice(confusion_responses)
        
        # 6. Handle THANKS
        if any(word in text for word in ['תודה', 'מעריך', 'תודה רבה', 'אסיר תודה']):
            thanks_responses = [
                "😊 בכיף! תמיד נעים לעזור!",
                "🙏 בבקשה! אני כאן בשבילך!",
                "❤️ שמחה שיכולתי לעזור!"
            ]
            return random.choice(thanks_responses)
        
        # 7. Handle HELP requests
        if any(word in text for word in ['עזור', 'עזרה', 'תוכל', 'תוכלי', 'אפשר', 'בעיה']):
            help_responses = [
                f"בוודאי{name_suffix}! במה בדיוק אוכל לעזור לך?",
                "אני כאן לעזור! 💪 תגיד לי מה אתה צריך.",
                "אשמח לסייע! 😊 איך אוכל לעזור לך?"
            ]
            return random.choice(help_responses)
        
        # 8. Handle specific questions about Maya
        if any(phrase in text for phrase in ['מי את', 'מה את', 'איך קוראים לך', 'מה השם שלך']):
            maya_responses = [
                "אני מאיה! 🤖 העוזרת הדיגיטלית שלך. אני כאן לעזור עם שאלות ומידע.",
                "שמי מאיה! 😊 אני בוט חכם שנועד לעזור לך עם כל מה שאתה צריך.",
                "אני מאיה - המזכירה הדיגיטלית שלך! 💼 איך אוכל לסייע לך?"
            ]
            return random.choice(maya_responses)
        
        # 9. DEFAULT - Unknown requests
        default_responses = [
            f"🤔 מעניין{name_suffix}! תוכל לספר לי עוד על זה?",
            "לא בטוחה שהבנתי לגמרי. איך אוכל לעזור לך?",
            f"זה נושא מעניין{name_suffix}! תוכל להסביר מה בדיוק אתה מחפש?",
            "אני עדיין לומדת! 📚 תוכל לנסח את השאלה אחרת?"
        ]
        return random.choice(default_responses)

# Bot instance
maya = MayaBot()

def send_message(chat_id, text):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False

@app.route("/")
def home():
    time_info = maya.get_israel_time()
    return jsonify({
        "status": "🤖 Maya Bot - Fixed Logic!",
        "version": "2.0 - Smart Responses",
        "current_time": time_info['full'],
        "users_with_names": len(maya.user_names),
        "features": [
            "✅ Clear time/date responses",
            "✅ Intelligent conversation",
            "✅ User name memory",
            "✅ Confusion handling",
            "✅ Hebrew support"
        ]
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
            logger.info(f"User {user_id}: {text[:40]}...")
            response = maya.process_message(user_id, text)
            logger.info(f"Response: {response[:40]}...")
            send_message(chat_id, response)
        
        return "OK"
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ERROR"

@app.route("/test")
def test():
    test_cases = {
        "מה השעה": maya.process_message(999, "מה השעה"),
        "מה התאריך היום": maya.process_message(999, "מה התאריך היום"),
        "שלום": maya.process_message(999, "שלום"),
        "שמי דוד": maya.process_message(999, "שמי דוד"),
        "מה שלומך": maya.process_message(999, "מה שלומך"),
        "לא הגיון": maya.process_message(999, "לא הגיון")
    }
    
    return jsonify({
        "message": "Test responses for Maya:",
        "tests": test_cases
    })

if __name__ == "__main__":
    logger.info("🚀 Starting Maya Bot - Fixed Logic Version")
    app.run(host="0.0.0.0", port=PORT, debug=False)
