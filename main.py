import os
import asyncio
from telegram import Update
from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
ContextTypes,
filters,
)
from flask import Flask, jsonify
import threading
import time

# Import מאיה החכמה

from intelligent_maya import (
init_intelligent_maya, intelligent_maya,
smart_response, get_user_insights, explain_thinking,
get_maya_status, run_maya_tests
)

# משתני סביבה

TELEGRAM_BOT_TOKEN = os.getenv(“TELEGRAM_BOT_TOKEN”)
GEMINI_API_KEY = os.getenv(“GEMINI_API_KEY”)
PORT = int(os.getenv(“PORT”, 10000))

# Flask app לhealth check

app = Flask(**name**)

@app.route(’/health’)
def health_check():
return jsonify({“status”: “healthy”, “service”: “maya-ai-agent”})

@app.route(’/’)
def home():
return jsonify({
“message”: “Maya AI Agent is running!”,
“status”: “active”,
“version”: “2.0”
})

# משתנה גלובלי למאיה

maya_agent = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“התחלת שיחה עם מאיה החכמה”””
user_id = update.effective_user.id
username = update.effective_user.first_name or “חבר”

```
welcome_message = f"""
```

היי {username}! 🌟 אני מאיה החכמה!

🧠 **אני AI Agent אמיתי - לא רק chatbot:**
✨ זוכרת הכל עליך
🎯 מבינה מה אתה באמת רוצה
💫 לומדת ומשתפרת מכל שיחה
🤗 תמיד חמה ותומכת
🛠️ יכולה להשתמש בכלים לעזור לך

**מה אני יכולה לעשות:**
📚 לענות על שאלות עם הבנה עמוקה
💡 לזכור דברים שאמרת לי
🎭 להבין איך אתה מרגיש
📋 לעזור עם מטלות ותכנון
🔍 לחפש מידע אם צריך
💬 פשוט לשוחח בצורה טבעית

איך אני יכולה לעזור לך היום?
“””

```
await update.message.reply_text(welcome_message)
```

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“טיפול בהודעות עם מאיה החכמה”””
user_id = update.effective_user.id
message = update.message.text

```
try:
    # תגובה חכמה ממאיה
    response = await smart_response(user_id, message)
    await update.message.reply_text(response)
    
except Exception as e:
    print(f"❌ שגיאה בטיפול בהודעה: {e}")
    await update.message.reply_text(
        "אוי... משהו השתבש בחשיבה שלי 😅 בואי ננסה שוב?"
    )
```

async def handle_insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“הצגת תובנות על המשתמש”””
user_id = update.effective_user.id

```
try:
    insights = await get_user_insights(user_id)
    
    if insights:
        message = f"""
```

🎯 **התובנות שלי עליך:**

👤 **פרופיל:**

- שלב יחסים: {insights[‘user_profile’][‘relationship_stage’]}
- מצב רגשי: {insights[‘user_profile’][‘emotional_state’]}
- סה”כ שיחות: {insights[‘user_profile’][‘total_conversations’]}
- זיכרונות: {insights[‘user_profile’][‘total_memories’]}

🗣️ **פעילות אחרונה:**

- שיחה אחרונה: {insights[‘recent_activity’][‘last_conversation’]}
- רמת מעורבות: {insights[‘recent_activity’][‘engagement_level’]}

😊 **ניתוח רגשי:**

- רגשות דומיננטים: {insights[‘emotional_analysis’][‘dominant_emotions’]}
- יציבות רגשית: {insights[‘emotional_analysis’][‘emotional_stability’]}
- מגמה: {insights[‘emotional_analysis’][‘recent_emotional_trend’]}

💡 **המלצות:**
“””

```
        for recommendation in insights['recommendations']:
            message += f"- {recommendation}\n"
        
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("עדיין לא יש לי מספיק מידע עליך. בואי נשוחח עוד!")
        
except Exception as e:
    print(f"❌ שגיאה בקבלת תובנות: {e}")
    await update.message.reply_text("לא הצלחתי לאסוף תובנות כרגע...")
```

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“הצגת סטטוס מאיה”””
try:
status = get_maya_status()

```
    if status.get("status") == "לא מאותחלת":
        await update.message.reply_text("❌ מאיה עדיין לא מאותחלת")
        return
    
    message = f"""
```

🤖 **סטטוס מאיה:**

📛 **שם:** {status[‘agent_name’]}
🔧 **גרסה:** {status[‘version’]}

⚙️ **מרכיבים:**
“””

```
    for component, status_text in status['components'].items():
        message += f"- {component}: {status_text}\n"
    
    message += "\n💪 **יכולות:**\n"
    for capability in status['capabilities']:
        message += f"- {capability}\n"
    
    await update.message.reply_text(message)
    
except Exception as e:
    print(f"❌ שגיאה בהצגת סטטוס: {e}")
    await update.message.reply_text("לא הצלחתי לקבל סטטוס...")
```

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“עזרה”””
help_text = “””
🆘 **עזרה - פקודות מאיה:**

📝 **פקודות בסיסיות:**

- פשוט תכתב לי - אני אבין ואענה
- /start - התחלה מחדש
- /help - העזרה הזו

🔍 **פקודות מתקדמות:**

- /insights - תובנות עליך
- /status - סטטוס המערכת

💡 **טיפים:**

- תכתב בצורה טבעית - אני אבין
- שתף אותי במידע עליך - אני אזכור
- בטח באמפתיה שלי - אני כאן בשבילך
- שאל הכל - אני אחפש תשובות

🎯 **מה אני יכולה לעשות:**

- להבין איך אתה מרגיש
- לזכור דברים חשובים
- לעזור עם מטלות
- לחפש מידע
- פשוט לשוחח טבעית
  “””
  
  await update.message.reply_text(help_text)

async def on_startup(app: Application):
“”“אתחול מאיה כשהבוט מתחיל”””
global maya_agent

```
print("🚀 מאתחל מאיה AI Agent חכם על Render...")

# מחיקת webhook
await app.bot.delete_webhook(drop_pending_updates=True)

# אתחול מאיה
maya_agent = init_intelligent_maya(GEMINI_API_KEY)

print("✅ מאיה AI Agent חכם מוכנה על Render!")
print("🎯 מאיה מבינה, זוכרת ולומדת מכל שיחה")
print("💫 מאיה רצה על Render עם יכולות מלאות!")
```

def run_flask():
“”“הרצת Flask server”””
app.run(host=‘0.0.0.0’, port=PORT, debug=False)

def main():
“”“הפעלת הבוט”””

```
# בדיקת משתנים
if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN לא מוגדר")
    return

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY לא מוגדר")
    return

# הפעלת Flask ברקע
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# יצירת אפליקציה
telegram_app = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .post_init(on_startup)
    .build()
)

# הוספת handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", handle_help))
telegram_app.add_handler(CommandHandler("insights", handle_insights))
telegram_app.add_handler(CommandHandler("status", handle_status))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# הדפסת מידע
print("=" * 60)
print("🌟 מאיה AI Agent חכם מתחיל על Render!")
print("=" * 60)
print("✅ מערכת זיכרון מתקדמת")
print("✅ הבנה מהקשרית עמוקה")
print("✅ אישיות חמה ונעימה")
print("✅ למידה רציפה")
print("✅ כלים מתקדמים")
print("✅ תמיכה רגשית")
print(f"✅ רץ על Render פורט {PORT}")
print("=" * 60)
print("🎯 מאיה מוכנה לשיחות חכמות!")
print("💫 תהנה מחוויית AI מתקדמת!")
print("=" * 60)

# הפעלת הבוט
telegram_app.run_polling()
```

if **name** == “**main**”:
main()