import os
import json
import threading
from datetime import datetime
import pytz
import telebot
import google.generativeai as genai
from http.server import HTTPServer, BaseHTTPRequestHandler

# Settings with ONLY normal quotes

TELEGRAM_TOKEN = os.getenv(‘TELEGRAM_TOKEN’)
GEMINI_API_KEY = os.getenv(‘GEMINI_API_KEY’)

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
print(‘Missing tokens!’)
exit(1)

# Setup Gemini

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(‘gemini-1.5-flash’)

# Create bot

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Memory

user_data = {}
chats = {}

def save_data():
try:
with open(‘data.json’, ‘w’, encoding=‘utf-8’) as f:
json.dump(user_data, f, ensure_ascii=False)
except Exception as e:
print(f’Save error: {e}’)

def load_data():
global user_data
try:
with open(‘data.json’, ‘r’, encoding=‘utf-8’) as f:
user_data = json.load(f)
print(f’Loaded memory for {len(user_data)} users’)
except:
user_data = {}
print(‘Creating new memory’)

def get_time_israel():
tz = pytz.timezone(‘Asia/Jerusalem’)
now = datetime.now(tz)
return now.strftime(’%H:%M’), now.strftime(’%A %d/%m/%Y’)

def extract_user_info(user_id, text):
user_id = str(user_id)

```
if user_id not in user_data:
    user_data[user_id] = {}

# Name detection
if 'קוראים לי' in text:
    try:
        parts = text.split('קוראים לי')
        if len(parts) > 1:
            name_part = parts[1].strip().split()[0]
            user_data[user_id]['שם'] = name_part.replace(',', '').replace('.', '')
            save_data()
            print(f'Remembered name: {user_data[user_id]["שם"]}')
            return True
    except:
        pass

return False
```

def quick_answers(text):
text_lower = text.lower()

```
# Time questions
if any(phrase in text_lower for phrase in ['מה השעה', 'איזה שעה', 'כמה השעה']):
    time_now, _ = get_time_israel()
    return f'🕐 השעה עכשיו בישראל: {time_now}'

# Date questions
if any(phrase in text_lower for phrase in ['מה התאריך', 'איזה תאריך', 'מה היום']):
    _, date_now = get_time_israel()
    return f'📅 התאריך היום: {date_now}'

# Weather simple
if 'מזג אוויר' in text_lower:
    if 'ניו יורק' in text_lower:
        return '🌤️ בניו יורק בדרך כלל בחורף קר (בערך 5°C) ובקיץ חם (בערך 25°C)'
    elif 'תל אביב' in text_lower:
        return '☀️ בתל אביב בדרך כלל חם ושמש, בחורף 18°C ובקיץ 30°C'
    else:
        return '🌍 איזו עיר אתה רוצה לדעת?'

return None
```

def create_smart_prompt(user_id):
time_now, date_now = get_time_israel()
user_info = user_data.get(str(user_id), {})
user_name = user_info.get(‘שם’, ‘חבר’)

```
prompt = f'''את מאיה - עוזרת חכמה וחמודה! 🌟
```

זמן: {time_now} | תאריך: {date_now}
המשתמש: {user_name}
מידע: {json.dumps(user_info, ensure_ascii=False)}

הוראות:

1. תני תשובות קצרות (1-2 שורות בלבד!)
1. השתמשי בשם {user_name}
1. תהיי חמודה אבל לא מוגזמת
1. תני עצות מעשיות וחכמות

תגיבי בצורה אישית וחכמה!’’’

```
return prompt
```

def start_chat(user_id):
try:
chat = model.start_chat(history=[])
prompt = create_smart_prompt(user_id)
chat.send_message(prompt)
return chat
except Exception as e:
print(f’Chat creation error: {e}’)
return None

# Health server

class HealthServer(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(200)
self.end_headers()
self.wfile.write(b’Maya Bot Running!’)
def log_message(self, *args):
pass

def run_server():
port = int(os.environ.get(‘PORT’, 10000))
server = HTTPServer((‘0.0.0.0’, port), HealthServer)
print(f’Health server running on port {port}’)
server.serve_forever()

# Message handling

@bot.message_handler(func=lambda m: True)
def handle_message(message):
user_id = str(message.from_user.id)
text = message.text

```
# Quick answers
quick_answer = quick_answers(text)
if quick_answer:
    bot.reply_to(message, quick_answer)
    return

# Save user info
info_saved = extract_user_info(user_id, text)

# Create chat if needed
if user_id not in chats:
    chats[user_id] = start_chat(user_id)

# Refresh if new info
if info_saved:
    chats[user_id] = start_chat(user_id)

if not chats[user_id]:
    bot.reply_to(message, '😅 יש לי בעיה טכנית, נסה שוב!')
    return

try:
    bot.send_chat_action(message.chat.id, 'typing')
    response = chats[user_id].send_message(text)
    bot.reply_to(message, response.text)
    
except Exception as e:
    print(f'Error: {e}')
    chats[user_id] = start_chat(user_id)
    bot.reply_to(message, '😅 רגע, אני מתרעננת... נסה שוב!')
```

# Commands

@bot.message_handler(commands=[‘memory’])
def memory_cmd(message):
user_id = str(message.from_user.id)
info = user_data.get(user_id, {})
if info:
text = ‘🧠 מה שאני זוכרת עליך:\n’
for key, value in info.items():
text += f’• {key}: {value}\n’
bot.reply_to(message, text)
else:
bot.reply_to(message, ‘🤔 עדיין לא זכרתי עליך הרבה. ספר לי על עצמך!’)

@bot.message_handler(commands=[‘forget’])
def forget_cmd(message):
user_id = str(message.from_user.id)
if user_id in user_data:
del user_data[user_id]
save_data()
if user_id in chats:
del chats[user_id]
bot.reply_to(message, ‘🧹 שכחתי הכל עליך! בואו נכיר מחדש!’)

@bot.message_handler(commands=[‘time’])
def time_cmd(message):
time_now, date_now = get_time_israel()
bot.reply_to(message, f’🕐 {time_now}\n📅 {date_now}’)

def main():
print(‘Maya starting…’)

```
# Clean webhook
try:
    bot.remove_webhook()
    print('Webhook cleaned')
except:
    pass

# Load data
load_data()

# Start server
threading.Thread(target=run_server, daemon=True).start()

print('Maya ready!')
print('Try: קוראים לי דוד or מה השעה?')

# Start bot
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f'Error: {e}')
        import time
        time.sleep(5)
```

if **name** == ‘**main**’:
main()