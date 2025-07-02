import os
import json
import threading
from datetime import datetime
import pytz
import telebot
import google.generativeai as genai
from http.server import HTTPServer, BaseHTTPRequestHandler

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
print(“💾 נתונים נשמרו”)
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

def extract_user_info(user_id, text):
“”“מזהה ושומר מידע על המשתמש - עם debug”””
user_id = str(user_id)

```
if user_id not in user_data:
    user_data[user_id] = {}

# זיהוי שם - מיוחד לעברית
text_lower = text.lower()

if 'קוראים לי' in text:
    try:
        # חיפוש המילה שאחרי "קוראים לי"
        parts = text.split('קוראים לי')
        if len(parts) > 1:
            name_part = parts[1].strip().split()[0]  # המילה הראשונה
            user_data[user_id]['שם'] = name_part.replace(',', '').replace('.', '')
            save_data()
            print(f"✅ זוכר שם: {user_data[user_id]['שם']}")
            return True
    except:
        pass

# זיהוי עבודה
if any(word in text_lower for word in ['עובד ב', 'עובדת ב', 'עבודה ב']):
    user_data[user_id]['עבודה'] = text[:100]  # שומר חלק מההודעה
    save_data()
    print(f"✅ זוכר עבודה למשתמש {user_id}")
    return True

return False
```

def quick_answers(text):
“”“תשובות מיידיות לשאלות פשוטות”””
text_lower = text.lower()

```
# שאלות שעה
if any(phrase in text_lower for phrase in ['מה השעה', 'איזה שעה', 'כמה השעה', 'שעה']):
    time_now, _ = get_time_israel()
    return f"🕐 השעה עכשיו: {time_now}"

# שאלות תאריך
if any(phrase in text_lower for phrase in ['מה התאריך', 'איזה תאריך', 'מה היום']):
    _, date_now = get_time_israel()
    return f"📅 התאריך היום: {date_now}"

# מזג אוויר בסיסי (ללא API)
if 'מזג אוויר' in text_lower or 'טמפרטורה' in text_lower:
    if 'ניו יורק' in text_lower:
        return "🌤️ בניו יורק עכשיו בערך 15°C (אני לא יכולה לבדוק בזמן אמת)"
    elif 'תל אביב' in text_lower:
        return "☀️ בתל אביב בדרך כלל חם ושמש, בערך 25°C"
    else:
        return "🌍 איזו עיר אתה רוצה לדעת?"

return None
```

def create_smart_prompt(user_id):
“”“יוצר prompt חכם עם המידע על המשתמש”””
time_now, date_now = get_time_israel()
user_info = user_data.get(str(user_id), {})

```
user_name = user_info.get('שם', 'חבר')

prompt = f"""את מאיה - עוזרת חכמה וחמודה! 🌟
```

זמן: {time_now} | תאריך: {date_now}
המשתמש: {user_name}

מידע שיש לי על {user_name}: {json.dumps(user_info, ensure_ascii=False)}

הוראות:

1. תני תשובות קצרות (1-2 שורות בלבד!)
1. השתמשי בשם {user_name} כשמתאים
1. תהיי חמודה אבל לא מוגזמת
1. תני עצות מעשיות וחכמות
1. אל תחזרי על מידע שכבר נתת

תגיבי בצורה אישית וחכמה!”””

```
return prompt
```

def start_chat(user_id):
“”“יוצר chat session חדש”””
try:
chat = model.start_chat(history=[])
prompt = create_smart_prompt(user_id)
chat.send_message(prompt)
print(f”✅ יצרתי chat למשתמש {user_id}”)
return chat
except Exception as e:
print(f”❌ שגיאה ביצירת chat: {e}”)
return None

# שרת בריאות

class HealthServer(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(200)
self.end_headers()
self.wfile.write(b”Maya Bot Running!”)
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

# בדיקה לתשובה מהירה
quick_answer = quick_answers(text)
if quick_answer:
    bot.reply_to(message, quick_answer)
    print(f"⚡ תשובה מהירה נשלחה")
    return

# שמירת מידע על המשתמש
info_saved = extract_user_info(user_id, text)

# יצירת chat אם צריך
if user_id not in chats:
    chats[user_id] = start_chat(user_id)

# אם יש chat חדש אחרי שמירת מידע, ריענון
if info_saved:
    chats[user_id] = start_chat(user_id)
    print(f"🔄 ריעננתי chat למשתמש {user_id}")

if not chats[user_id]:
    bot.reply_to(message, "😅 יש לי בעיה טכנית, נסה שוב!")
    return

try:
    # שליחת typing
    bot.send_chat_action(message.chat.id, 'typing')
    
    # קבלת תגובה מ-Gemini
    response = chats[user_id].send_message(text)
    bot.reply_to(message, response.text)
    print(f"✅ תגובה נשלחה למשתמש {user_id}")
    
except Exception as e:
    print(f"❌ שגיאה: {e}")
    # ריענון chat במקרה של שגיאה
    chats[user_id] = start_chat(user_id)
    bot.reply_to(message, "😅 רגע, אני מתרעננת... נסה שוב!")
```

# פקודות

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

@bot.message_handler(commands=[‘forget’])
def forget_cmd(message):
user_id = str(message.from_user.id)
if user_id in user_data:
del user_data[user_id]
save_data()
if user_id in chats:
del chats[user_id]
bot.reply_to(message, “🧹 שכחתי הכל עליך! בואו נכיר מחדש!”)

@bot.message_handler(commands=[‘refresh’])
def refresh_cmd(message):
user_id = str(message.from_user.id)
chats[user_id] = start_chat(user_id)
bot.reply_to(message, “🔄 רעננתי את הזיכרון! עכשיו אני זוכרת הכל טוב יותר!”)

@bot.message_handler(commands=[‘time’])
def time_cmd(message):
time_now, date_now = get_time_israel()
bot.reply_to(message, f”🕐 {time_now}\n📅 {date_now}”)

def main():
print(“🚀 מאיה מתחילה…”)

```
# ניקוי webhook
try:
    bot.remove_webhook()
    print("✅ Webhook נוקה")
except:
    print("⚠️ לא הצלחתי לנקות webhook")

# טעינת נתונים
load_data()

# הפעלת שרת
threading.Thread(target=run_server, daemon=True).start()

print("🎉 מאיה מוכנה!")
print("💡 נסה לשלוח: 'קוראים לי דוד' או 'מה השעה?'")

# הפעלת הבוט
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        print("🔄 מנסה שוב בעוד 5 שניות...")
        import time
        time.sleep(5)
        try:
            bot.remove_webhook()
        except:
            pass
```

if **name** == ‘**main**’:
main()
