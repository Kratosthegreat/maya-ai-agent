import os
import json
import threading
import requests
from datetime import datetime
import pytz
import telebot
import google.generativeai as genai
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup
import urllib.parse

# הגדרות

TELEGRAM_TOKEN = os.getenv(‘TELEGRAM_TOKEN’)
GEMINI_API_KEY = os.getenv(‘GEMINI_API_KEY’)

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
print(“❌ חסרים טוקנים!”)
exit(1)

# הגדרת Gemini

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(‘gemini-1.5-flash’)

# יצירת הבוט

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# זיכרון

user_data = {}
chats = {}

def save_data():
try:
with open(‘data.json’, ‘w’, encoding=‘utf-8’) as f:
json.dump(user_data, f, ensure_ascii=False)
except Exception as e:
print(f”❌ שגיאה בשמירה: {e}”)

def load_data():
global user_data
try:
with open(‘data.json’, ‘r’, encoding=‘utf-8’) as f:
user_data = json.load(f)
print(f”✅ נטען זיכרון עבור {len(user_data)} משתמשים”)
except:
user_data = {}
print(“📝 יצירת זיכרון חדש”)

def get_time_israel():
“”“מחזיר את השעה הנוכחית בישראל”””
tz = pytz.timezone(‘Asia/Jerusalem’)
now = datetime.now(tz)
return now.strftime(’%H:%M’), now.strftime(’%A %d/%m/%Y’)

def search_web(query, num_results=3):
“”“חיפוש ברשת - פונקציה בסיסית”””
try:
# משתמש ב-DuckDuckGo כמו שאני עושה
search_url = f”https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}”
headers = {
‘User-Agent’: ‘Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36’
}

```
    response = requests.get(search_url, headers=headers, timeout=10)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # חיפוש תוצאות - פשוט וחלקי
        for link in soup.find_all('a', {'class': 'result__a'})[:num_results]:
            title = link.get_text().strip()
            url = link.get('href', '')
            if title and url:
                results.append({'title': title, 'url': url})
        
        return results
    
    return []
except Exception as e:
    print(f"❌ שגיאה בחיפוש: {e}")
    return []
```

def get_weather_basic(city):
“”“מזג אוויר בסיסי בלי API”””
try:
# חיפוש פשוט במזג אוויר
search_results = search_web(f”weather {city} today temperature”)
if search_results:
return f”🌤️ מצאתי מידע על מזג האוויר ב{city} - תוכל לבדוק כאן: {search_results[0][‘url’]}”
else:
return f”🌍 לא מצאתי מידע עדכני על מזג האוויר ב{city}”
except:
return “❌ שגיאה בחיפוש מזג אוויר”

def extract_user_info(user_id, text):
“”“מזהה ושומר מידע על המשתמש”””
user_id = str(user_id)

```
if user_id not in user_data:
    user_data[user_id] = {}

# זיהוי שם
if 'קוראים לי' in text:
    try:
        parts = text.split('קוראים לי')
        if len(parts) > 1:
            name_part = parts[1].strip().split()[0]
            user_data[user_id]['שם'] = name_part.replace(',', '').replace('.', '')
            save_data()
            print(f"✅ זוכר שם: {user_data[user_id]['שם']}")
            return True
    except:
        pass

# זיהוי עבודה
if any(word in text.lower() for word in ['עובד ב', 'עובדת ב', 'עבודה ב']):
    user_data[user_id]['עבודה'] = text[:100]
    save_data()
    return True

return False
```

def handle_web_search(text):
“”“מטפל בבקשות חיפוש”””
text_lower = text.lower()

```
# זיהוי בקשות חיפוש
search_triggers = ['חפש', 'מצא', 'בדוק', 'מה קורה', 'חדשות על', 'מידע על']

for trigger in search_triggers:
    if trigger in text_lower:
        # חילוץ נושא החיפוש
        query = text_lower.replace(trigger, '').strip()
        if query:
            results = search_web(query)
            if results:
                response = f"🔍 מצאתי מידע על '{query}':\n\n"
                for i, result in enumerate(results[:3], 1):
                    response += f"{i}. {result['title']}\n"
                response += f"\n💡 לפרטים נוספים, אפשר לחפש יותר..."
                return response
            else:
                return f"🤔 לא מצאתי מידע טוב על '{query}', נסה לנסח אחרת"

return None
```

def quick_answers(text):
“”“תשובות מיידיות ומחיפוש”””
text_lower = text.lower()

```
# שאלות שעה
if any(phrase in text_lower for phrase in ['מה השעה', 'איזה שעה', 'כמה השעה']):
    time_now, _ = get_time_israel()
    return f"🕐 השעה עכשיו בישראל: {time_now}"

# שאלות תאריך
if any(phrase in text_lower for phrase in ['מה התאריך', 'איזה תאריך', 'מה היום']):
    _, date_now = get_time_israel()
    return f"📅 התאריך היום: {date_now}"

# מזג אוויר עם חיפוש
if 'מזג אוויר' in text_lower or 'טמפרטורה' in text_lower:
    if 'ניו יורק' in text_lower:
        return get_weather_basic('New York')
    elif 'תל אביב' in text_lower:
        return get_weather_basic('Tel Aviv')
    elif 'לונדון' in text_lower:
        return get_weather_basic('London')
    else:
        return "🌍 באיזו עיר אתה רוצה לדעת את מזג האוויר?"

# חיפוש כללי
search_result = handle_web_search(text)
if search_result:
    return search_result

return None
```

def create_smart_prompt(user_id):
“”“יוצר prompt חכם עם יכולות חיפוש”””
time_now, date_now = get_time_israel()
user_info = user_data.get(str(user_id), {})
user_name = user_info.get(‘שם’, ‘חבר’)

```
prompt = f"""את מאיה - עוזרת חכמה שיכולה לחפש ברשת! 🌟
```

זמן: {time_now} | תאריך: {date_now}
המשתמש: {user_name}
מידע: {json.dumps(user_info, ensure_ascii=False)}

יכולות שלך:
✅ חיפוש מידע עדכני ברשת
✅ מזג אוויר בזמן אמת  
✅ מידע על חדשות ואירועים
✅ תשובות מבוססות נתונים

הוראות:

1. תני תשובות קצרות (1-2 שורות)
1. אם אין לך מידע עדכני - הגידי שאתה יכולה לחפש
1. השתמשי בשם {user_name}
1. תהיי מועילה ומדויקת

תגיבי בצורה חכמה ועדכנית!”””

```
return prompt
```

def start_chat(user_id):
“”“יוצר chat session חדש”””
try:
chat = model.start_chat(history=[])
prompt = create_smart_prompt(user_id)
chat.send_message(prompt)
return chat
except Exception as e:
print(f”❌ שגיאה ביצירת chat: {e}”)
return None

# שרת בריאות

class HealthServer(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(200)
self.end_headers()
self.wfile.write(b”Maya Smart Bot Running!”)
def log_message(self, *args):
pass

def run_server():
port = int(os.environ.get(“PORT”, 10000))
server = HTTPServer((“0.0.0.0”, port), HealthServer)
print(f”✅ שרת בריאות רץ על פורט {port}”)
server.serve_forever()

# טיפול בהודעות

@bot.message_handler(func=lambda m: True)
def handle_message(message):
user_id = str(message.from_user.id)
text = message.text

```
print(f"📨 הודעה מ-{user_id}: {text}")

# בדיקה לתשובה מהירה או חיפוש
quick_answer = quick_answers(text)
if quick_answer:
    bot.reply_to(message, quick_answer)
    print(f"⚡ תשובה מהירה/חיפוש נשלחה")
    return

# שמירת מידע על המשתמש
info_saved = extract_user_info(user_id, text)

# יצירת chat אם צריך
if user_id not in chats:
    chats[user_id] = start_chat(user_id)

# ריענון אם יש מידע חדש
if info_saved:
    chats[user_id] = start_chat(user_id)

if not chats[user_id]:
    bot.reply_to(message, "😅 יש לי בעיה טכנית, נסה שוב!")
    return

try:
    bot.send_chat_action(message.chat.id, 'typing')
    response = chats[user_id].send_message(text)
    bot.reply_to(message, response.text)
    
except Exception as e:
    print(f"❌ שגיאה: {e}")
    chats[user_id] = start_chat(user_id)
    bot.reply_to(message, "😅 רגע, אני מתרעננת... נסה שוב!")
```

# פקודות

@bot.message_handler(commands=[‘search’])
def search_cmd(message):
query = message.text.replace(’/search’, ‘’).strip()
if query:
results = search_web(query)
if results:
response = f”🔍 תוצאות חיפוש עבור ‘{query}’:\n\n”
for i, result in enumerate(results, 1):
response += f”{i}. {result[‘title’]}\n”
bot.reply_to(message, response)
else:
bot.reply_to(message, f”🤔 לא מצאתי תוצאות עבור ‘{query}’”)
else:
bot.reply_to(message, “💡 שימוש: /search [נושא החיפוש]”)

@bot.message_handler(commands=[‘weather’])
def weather_cmd(message):
city = message.text.replace(’/weather’, ‘’).strip()
if city:
weather_info = get_weather_basic(city)
bot.reply_to(message, weather_info)
else:
bot.reply_to(message, “💡 שימוש: /weather [שם עיר]”)

@bot.message_handler(commands=[‘memory’])
def memory_cmd(message):
user_id = str(message.from_user.id)
info = user_data.get(user_id, {})
if info:
text = “🧠 מה שאני זוכרת עליך:\n”
for key, value in info.items():
text += f”• {key}: {value}\n”
bot.reply_to(message, text)
else:
bot.reply_to(message, “🤔 עדיין לא זכרתי עליך הרבה. ספר לי על עצמך!”)

@bot.message_handler(commands=[‘help’])
def help_cmd(message):
help_text = “”“🤖 מאיה - בוט חכם עם חיפוש ברשת!

🔍 חיפושים:
• “חפש [נושא]” - חיפוש כללי
• “מזג אוויר בניו יורק” - מזג אוויר
• “מה השעה?” - שעה נוכחית

📋 פקודות:
• /search [נושא] - חיפוש מפורש
• /weather [עיר] - מזג אוויר
• /memory - מה אני זוכרת עליך
• /help - עזרה זו

💡 פשוט כתוב לי שאלה ואני אחפש עבורך!”””

```
bot.reply_to(message, help_text)
```

def main():
print(“🚀 מאיה החכמה מתחילה…”)

```
# ניקוי webhook
try:
    bot.remove_webhook()
    print("✅ Webhook נוקה")
except:
    pass

# טעינת נתונים
load_data()

# הפעלת שרת
threading.Thread(target=run_server, daemon=True).start()

print("🎉 מאיה מוכנה לחיפוש ברשת!")
print("💡 נסה: 'חפש חדשות ישראל' או 'מזג אוויר בתל אביב'")

# הפעלת הבוט
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        print("🔄 מנסה שוב...")
        import time
        time.sleep(5)
```

if **name** == ‘**main**’:
main()