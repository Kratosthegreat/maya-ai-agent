def _extract_location(self, message: str) -> str:
        """חילוץ מיקום מהודעה - משופר לערים מורכבות"""
        
        # רשימת ערים ומדינות מוכרות (כולל שמות מורכבים)
        known_locations = [
            # ערים ישראליות
            "חיפה", "תל אביב", "ירושלים", "באר שבע", "אילת", "נצרת", "טבריה", 
            "צפת", "אשדוד", "אשקלון", "רמת גן", "פתח תקווה", "נתניה", "הרצליה", 
            "רעננה", "כפר סבא", "רמלה", "לוד", "עפולה", "חדרה", "קריית שמונה",
            
            # ערים עולמיות מוכרות (כולל שמות מורכבים)
            "בואנוס איירס", "ניו יורק", "לוס אנג'לס", "סן פרנסיסקו", "לאס וגאס",
            "מיאמי", "שיקגו", "בוסטון", "סיאטל", "לונדון", "פריז", "ברלין", 
            "רומא", "מדריד", "אמסטרדם", "מוסקבה", "טוקיו", "בייג'ינג", "שנגחאי",
            "מומבאי", "דלהי", "סינגפור", "הונג קונג", "סידני", "מלבורן", "קייפ טאון",
            
            # מדינות
            "ארגנטינה", "ברזיל", "אמריקה", "ארצות הברית", "אנגליה", "צרפת", 
            "גרמניה", "איטליה", "ספרד", "רוסיה", "יפן", "סין", "הודו", "אוסטרליה"
        ]
        
        message_lower = message.lower()
        
        # חיפוש ערים/מדינות מוכרות בהודעה
        for location in known_locations:
            if location.lower() in message_lower:
                logger.debug(f"Found known location: {location}")
                return location
        
        # אם לא נמצא מיקום מוכר, נסה לחלץ מהטקסט
        # הסרת מיל# === מאיה 3.0 - בנייה מחדש מלאה ===
import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests
import pytz
from typing import Dict, Any, Optional
import time
import re

# Third-party imports
import google.generativeai as genai
from config import config

# === LOGGING ===
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# === DATA STORAGE ===
DATA_FILE = "maya_data.json"
GEMINI_USAGE_FILE = "gemini_usage.json"
user_data = {}
conversations = {}
memories = {}

def load_data():
    global user_data, conversations, memories
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_data = data.get('users', {})
                conversations = data.get('conversations', {})
                memories = data.get('memories', {})
                logger.info(f"Loaded data for {len(user_data)} users")
        else:
            logger.info("No existing data file, starting fresh")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        user_data = {}
        conversations = {}
        memories = {}

def save_data():
    try:
        data = {
            'users': user_data,
            'conversations': conversations,
            'memories': memories,
            'last_updated': datetime.now().isoformat()
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug("Data saved successfully")
    except Exception as e:
        logger.error(f"Error saving data: {e}")

load_data()

# === CLAUDE-LIKE INTELLIGENCE ENGINE ===
class ClaudeIntelligenceEngine:
    """מנוע חכמה שמחקה בדיוק את Claude"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        
        # בסיס ידע מובנה - כמו שיש לי
        self.built_in_knowledge = {
            # ידע ישראלי עדכני
            "israel_current_war": {
                "name": "מלחמת חרבות ברזל",
                "start": "7 באוקטובר 2023", 
                "against": "חמאס",
                "status": "מתמשכת",
                "quick_answer": "המלחמה האחרונה של ישראל היא מלחמת חרבות ברזל שהחלה ב-7 באוקטובר 2023 עם התקפת הטרור של חמאס."
            },
            
            # ידע ספורט
            "world_cup_2026": {
                "year": 2026,
                "hosts": ["ארצות הברית", "מקסיקו", "קנדה"], 
                "teams": 48,
                "quick_answer": "המונדיאל הבא יתקיים ב-2026 בארצות הברית, מקסיקו וקנדה עם 48 נבחרות."
            },
            
            "olympics_2028": {
                "year": 2028,
                "host": "לוס אנג'לס",
                "season": "קיץ",
                "quick_answer": "האולימפיאדה הבאה תהיה ב-2028 בלוס אנג'לס."
            },
            
            # ידע פוליטי עדכני
            "us_president": {
                "name": "דונלד טראמפ",
                "elected": "נובמבר 2024",
                "inaugurated": "ינואר 2025",
                "quick_answer": "הנשיא הנוכחי של ארצות הברית הוא דונלד טראמפ (נבחר בנובמבר 2024)."
            }
        }
        
        # דפוסי זיהוי חכמים
        self.recognition_patterns = {
            # זיהוי ברכות
            "greeting": [
                r"^(היי|שלום|hello|hi)\s*(מאיה)?$",
                r"^(בוקר טוב|ערב טוב|לילה טוב)$"
            ],
            
            # זיהוי שאלות על מצב
            "how_are_you": [
                r"(מה שלומך|איך אתה|איך את|מה נשמע|איך הולך)",
                r"(how are you|how's it going|what's up)"
            ],
            
            # זיהוי שאלות על מלחמה בישראל
            "israel_war": [
                r"(מלחמה|מלחמת).*(אחרון|עכשיו|נוכחי|היום|ישראל)",
                r"המלחמה.*(של ישראל|בישראל|עכשיו)",
                r"(7 באוקטובר|שבעה באוקטובר|חרבות ברזל)",
                r"(חמאס|עזה|דרום).*(מלחמה|קרב)"
            ],
            
            # זיהוי שאלות מונדיאל
            "world_cup": [
                r"(מונדיאל|world cup).*(הבא|2026|מתי)",
                r"(כדורגל|פוטבול).*(עולם|מונדיאל)"
            ],
            
            # זיהוי שאלות אולימפיאדה  
            "olympics": [
                r"(אולימפיאדה|olympics).*(הבא|2028|מתי)",
                r"(משחקים אולימפיים)"
            ],
            
            # זיהוי שאלות על נשיא ארצות הברית
            "us_president": [
                r"(נשיא|president).*(אמריקה|ארצות הברית|אמריקאי)",
                r"(טראמפ|trump)",
                r"מי (נשיא|מנהל|בראש).*(אמריקה|ארצות הברית)"
            ],
            
            # זיהוי שאלות מזג אוויר
            "weather": [
                r"(מזג אוויר|טמפרטורה|חם|קר|מעלות|גשם|שמש)",
                r"מה (הטמפרטורה|המזג|מזג האוויר)",
                r"(טמפרטורה|מזג אוויר).*(ב|של|עכשיו)",
                r"כמה מעלות",
                r"איך (המזג|מזג האוויר|הטמפרטורה)"
            ],
            
            # זיהוי שאלות זמן
            "time": [
                r"(שעה|זמן|מתי עכשיו)"
            ]
        }
    
    def analyze_and_respond(self, message: str) -> Dict[str, Any]:
        """ניתוח הודעה והחזרת תשובה - כמו שאני עובד"""
        
        message_lower = message.lower().strip()
        
        # בדיקה האם יש תשובה מובנית מוכנה
        for topic, patterns in self.recognition_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    logger.info(f"Detected topic: {topic}")
                    return self._get_built_in_response(topic, message)
        
            else:
                # אין תשובה מובנית - בדוק אם צריך חיפוש או AI
                return self._determine_next_action(message, message_lower)
        
        # אם אין תשובה מובנית - זה יחזור לשיחה רגילה או חיפוש
        return {
            "type": "needs_search_or_ai",
            "confidence": "low",
            "response": None
        }
    
    def _determine_next_action(self, original_message: str, message_lower: str) -> Dict[str, Any]:
        """קביעה מה לעשות כשאין תשובה מובנית"""
        
        # שאלות שדורשות חיפוש באינטרנט
        search_indicators = [
            "מה קורה", "מה חדש", "עדכונים", "חדשות",
            "מי זה", "מי זאת", "מה זה", "איפה", "מתי",
            "כמה עולה", "מחיר", "עלות", "מחירים"
        ]
        
        # שאלות מזג אוויר על מקומות לא מוכרים
        weather_but_unknown = any(word in message_lower for word in ["טמפרטורה", "מזג אוויר", "מעלות", "חם", "קר"])
        
        # אם זה נראה כמו שאלה שדורשת מידע עדכני
        if any(indicator in message_lower for indicator in search_indicators) or weather_but_unknown:
            return {
                "type": "needs_web_search",
                "confidence": "high",
                "response": None
            }
        
        # אחרת, עבור ל-AI רגיל
        return {
            "type": "needs_ai_or_search",
            "confidence": "medium", 
            "response": None
        }
    
    def _get_built_in_response(self, topic: str, original_message: str) -> Dict[str, Any]:
        """קבלת תשובה מובנית - בסגנון שלי"""
        
        if topic == "greeting":
            response = "היי! 👋"
            
        elif topic == "how_are_you":
            response = "בסדר גמור! 😊"
            
        elif topic == "israel_war":
            response = "מלחמת חרבות ברזל - המלחמה שהחלה ב-7 באוקטובר 2023 כשחמאס תקף את ישראל. זו המלחמה הנוכחית של ישראל."
            
        elif topic == "world_cup":
            response = "המונדיאל הבא ב-2026! 🏆\nארצות הברית, מקסיקו וקנדה יארחו יחד.\n48 נבחרות במקום 32 - המונדיאל הגדול ביותר בהיסטוריה."
            
        elif topic == "olympics":
            response = "אולימפיאדת הקיץ הבאה ב-2028 בלוס אנג'לס! 🏅\nהשלישית שלהם בעיר הזו."
            
        elif topic == "us_president":
            response = "דונלד טראמפ הוא הנשיא הנוכחי של ארצות הברית. נבחר בנובמבר 2024 ונכנס לתפקיד בינואר 2025."
            
        elif topic == "weather":
            return {
                "type": "weather_service", 
                "confidence": "high",
                "response": None
            }
            
        elif topic == "time":
            return {
                "type": "time_service",
                "confidence": "high", 
                "response": None
            }
        
        else:
            response = "אין מידע זמין"
        
        return {
            "type": "direct_answer",
            "confidence": "high",
            "response": response,
            "source": "built_in_knowledge"
        }

# === GEMINI TRACKER ===
class GeminiTracker:
    def __init__(self):
        self.usage_file = GEMINI_USAGE_FILE
        self.daily_limit = 1500
        self.minute_limit = 15
        self.load_usage_data()
    
    def load_usage_data(self):
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    self.usage_data = json.load(f)
            except:
                self._init_usage_data()
        else:
            self._init_usage_data()
    
    def _init_usage_data(self):
        self.usage_data = {
            'daily_requests': 0,
            'last_reset': str(datetime.now().date()),
            'minute_requests': [],
            'total_tokens': 0,
            'total_requests_ever': 0
        }
    
    def save_usage_data(self):
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage: {e}")
    
    def can_make_request(self):
        today = str(datetime.now().date())
        if self.usage_data['last_reset'] != today:
            self.usage_data['daily_requests'] = 0
            self.usage_data['last_reset'] = today
            self.usage_data['minute_requests'] = []
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        self.usage_data['minute_requests'] = [
            req_time for req_time in self.usage_data['minute_requests']
            if datetime.fromisoformat(req_time) > minute_ago
        ]
        
        if self.usage_data['daily_requests'] >= self.daily_limit:
            return False, f"הגעת למגבלה היומית ({self.daily_limit})"
        if len(self.usage_data['minute_requests']) >= self.minute_limit:
            return False, f"יותר מדי בקשות בדקה ({self.minute_limit})"
        
        return True, "OK"
    
    def record_request(self, tokens_used=0):
        now = datetime.now()
        self.usage_data['daily_requests'] += 1
        self.usage_data['total_requests_ever'] += 1
        self.usage_data['minute_requests'].append(now.isoformat())
        self.usage_data['total_tokens'] += tokens_used
        self.save_usage_data()
    
    def get_usage_stats(self):
        return {
            'daily_requests': self.usage_data['daily_requests'],
            'daily_limit': self.daily_limit,
            'daily_remaining': self.daily_limit - self.usage_data['daily_requests'],
            'total_tokens': self.usage_data['total_tokens'],
            'total_requests_ever': self.usage_data['total_requests_ever'],
            'percentage_used_today': round((self.usage_data['daily_requests'] / self.daily_limit) * 100, 1)
        }

# === CLAUDE-STYLE AI SERVICE ===
class ClaudeStyleAI:
    """שירות AI שמחקה את Claude בדיוק"""
    
    def __init__(self):
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            self.chat_sessions = {}
            self.intelligence_engine = ClaudeIntelligenceEngine()
            self.tracker = GeminiTracker()
            
            # הוראות מערכת מחודשות - בדיוק כמו שאני מתנהג
            self.system_prompt = """את מאיה - עוזרת AI פשוטה וישירה.

חוקים קריטיים:
1. אל תברכי אוטומטית! אל תגידי "שלום" או "היי" אלא אם המשתמש בירך קודם
2. תשובות קצרות - משפט אחד או שניים לכל היותר
3. אל תשאלי שאלות מיותרות כמו "מה שלומך?" או "איך אני יכולה לעזור?"
4. תני תשובות ישירות ולעניין
5. אל תכפילי הודעות

דוגמאות:
שאלה: "מה שלומך?"
תשובה: "בסדר גמור! 😊"

שאלה: "היי מאיה"  
תשובה: "היי! 👋"

שאלה: "מתי המונדיאל הבא?"
תשובה: "ב-2026 בארצות הברית, מקסיקו וקנדה 🏆"

תגיבי רק למה שנשאל ותהיי קצרה ומדויקת."""
            
            logger.info("Claude-style AI Service initialized")
            
        except Exception as e:
            logger.error(f"AI Service initialization failed: {e}")
            raise
    
    def generate_response(self, user_id: str, message: str, context: str = "") -> str:
        try:
            # בדיקת מגבלות
            can_request, status_message = self.tracker.can_make_request()
            if not can_request:
                return f"יותר מדי בקשות היום. נסה מאוחר יותר! 😊"
            
            # שלב 1: בדיקה אם יש תשובה מובנית
            intelligence_result = self.intelligence_engine.analyze_and_respond(message)
            
            if intelligence_result["type"] == "direct_answer":
                # יש תשובה מוכנה - החזר אותה!
                self.tracker.record_request(0)  # לא השתמשנו ב-API
                return intelligence_result["response"]
            
            elif intelligence_result["type"] == "weather_service":
                location = self._extract_location(message)
                weather_result = weather_service.get_weather_anywhere(location)
                # אם שירות מזג האוויר נכשל, נסה חיפוש באינטרנט
                if "בעיה" in weather_result or "לא מצאתי" in weather_result:
                    logger.info(f"Weather service failed for {location}, trying web search")
                    search_query = f"weather temperature {location} now"
                    search_result = web_search_service.search_web(search_query)
                    return search_result if search_result else weather_result
                return weather_result
            
            elif intelligence_result["type"] == "time_service":
                return self._get_current_time()
            
            elif intelligence_result["type"] == "needs_web_search":
                # חיפוש באינטרנט מיידי
                logger.info(f"Performing web search for: {message}")
                search_result = web_search_service.search_web(message)
                if len(search_result) > 50 and "לא מצאתי" not in search_result:
                    return search_result
                else:
                    # אם החיפוש נכשל, עבור ל-AI
                    return self._generate_ai_response(message, context, user_id)
            
            else:
                # אין תשובה מובנית - עבור ל-AI או חיפוש
                return self._generate_ai_response(message, context, user_id)
                
        except Exception as e:
            logger.error(f"Generate response error: {e}")
            return "משהו השתבש. בוא ננסה שוב? 🤔"
    
    def _extract_location(self, message: str) -> str:
        """חילוץ מיקום מהודעה - משופר לערים מורכבות"""
        
        # רשימת ערים ומדינות מוכרות (כולל שמות מורכבים)
        known_locations = [
            # ערים ישראליות
            "חיפה", "תל אביב", "ירושלים", "באר שבע", "אילת", "נצרת", "טבריה", 
            "צפת", "אשדוד", "אשקלון", "רמת גן", "פתח תקווה", "נתניה", "הרצליה", 
            "רעננה", "כפר סבא", "רמלה", "לוד", "עפולה", "חדרה", "קריית שמונה",
            
            # ערים עולמיות מוכרות (כולל שמות מורכבים)
            "בואנוס איירס", "ניו יורק", "לוס אנג'לס", "סן פרנסיסקו", "לאס וגאס",
            "מיאמי", "שיקגו", "בוסטון", "סיאטל", "לונדון", "פריז", "ברלין", 
            "רומא", "מדריד", "אמסטרדם", "מוסקבה", "טוקיו", "בייג'ינג", "שנגחאי",
            "מומבאי", "דלהי", "סינגפור", "הונג קונג", "סידני", "מלבורן", "קייפ טאון",
            
            # מדינות
            "ארגנטינה", "ברזיל", "אמריקה", "ארצות הברית", "אנגליה", "צרפת", 
            "גרמניה", "איטליה", "ספרד", "רוסיה", "יפן", "סין", "הודו", "אוסטרליה"
        ]
        
        message_lower = message.lower()
        
        # חיפוש ערים/מדינות מוכרות בהודעה
        for location in known_locations:
            if location.lower() in message_lower:
                logger.debug(f"Found known location: {location}")
                return location
        
        # אם לא נמצא מיקום מוכר, נסה לחלץ מהטקסט
        # הסרת מילות מפתח נפוצות
        clean_text = message.replace("מזג אוויר", "").replace("טמפרטורה", "")
        clean_text = clean_text.replace("מה ה", "").replace("מה ", "")
        clean_text = clean_text.replace("ב", "").replace("של", "").replace("את", "")
        clean_text = clean_text.replace("עכשיו", "").replace("היום", "")
        clean_text = clean_text.strip()
        
        if not clean_text or len(clean_text) < 2:
            return "תל אביב"  # ברירת מחדל
        return clean_text
    
    def _get_current_time(self) -> str:
        """קבלת זמן נוכחי"""
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        return f"🕐 {now.strftime('%H:%M')}"
    
    def _generate_ai_response(self, message: str, context: str, user_id: str) -> str:
        """יצירת תשובה עם AI - בסגנון Claude"""
        
        # הכנת הודעה משופרת
        enhanced_message = f"""
        {self.system_prompt}
        
        הקשר משתמש: {context}
        הודעת המשתמש: {message}
        
        תני תשובה קצרה וטבעית כמו Claude.
        """
        
        try:
            # שימוש ב-AI
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
            
            chat = self.chat_sessions[user_id]
            response = chat.send_message(enhanced_message)
            
            self.tracker.record_request(len(response.text))
            
            # ניקוי התשובה מדברים מיותרים
            cleaned_response = self._clean_ai_response(response.text)
            return cleaned_response
            
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return "לא הצלחתי לעבד את זה. נסה שאלה אחרת 🤔"
    
    def _clean_ai_response(self, response: str) -> str:
        """ניקוי תשובת AI מדברים מיותרים"""
        
        # הסרת ברכות אוטומטיות בתחילת התשובה
        unwanted_starts = [
            "שלום דוד", "שלום!", "היי!", "הי דוד", "היי דוד",
            "שמחה לעזור", "אני כאן בשבילך", "🤖 היי David! אני מאיה",
            "היי David!", "אני מאיה"
        ]
        
        for unwanted in unwanted_starts:
            if response.strip().startswith(unwanted):
                response = response.replace(unwanted, "").strip()
                if response.startswith(","):
                    response = response[1:].strip()
                if response.startswith("!"):
                    response = response[1:].strip()
        
        # הסרת שאלות מיותרות בסוף
        unwanted_endings = [
            "מה שלומך?", "איך אני יכולה לעזור?", "איך אוכל לעזור?",
            "מה אתה צריך?", "במה אוכל לסייע?"
        ]
        
        for unwanted in unwanted_endings:
            if response.strip().endswith(unwanted):
                response = response.replace(unwanted, "").strip()
        
        # קיצור תשובות ארוכות מדי - רק 2 משפטים
        sentences = response.split('.')
        if len(sentences) > 2:
            response =
