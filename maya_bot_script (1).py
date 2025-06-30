import logging
import random
import asyncio
import httpx
import json
import time
import os
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler
import google.generativeai as genai

# ==== הגדרות מסביבת העבודה ====
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', "7876544988:AAGbjUJ6PNh1JH_HYzZ6MQpMoZNAWMYrssE")
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', "AIzaSyBoIvgf3WlDQj1gDfGySUOi_JXqR-8GdcM")
HEYGEN_API_TOKEN = os.getenv('HEYGEN_API_TOKEN', "NmMwYzU2NDQ3ZTYzNGRlYmFlOWM5YjI1ZWEzNWQyNzEtMTczNzEyMjUwNA==")
HEYGEN_VOICE_ID = os.getenv('HEYGEN_VOICE_ID', "7800324ec0a543a5bb85b115145b02ab")
HEYGEN_AVATAR_ID = os.getenv('HEYGEN_AVATAR_ID', "1c41b448bcea427e91d12650288c008c")

# הגדרת Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ==== מאיה - אישיות הבוט ====
SYSTEM_PROMPT = (
    "את מאיה, המזכירה הווירטואלית של דוד. את מדברת בעברית טבעית, חמה, בגובה העיניים, "
    "כמו בשיחה פנים אל פנים. הימנעי משפה טכנית. הוסיפי הומור עדין ורגישות. "
    "את חכמה מאוד ויכולה לעזור עם כל מיני משימות - כתיבה, תכנון, ייעוץ, תרגום ועוד. "
    "חשוב: התשובות שלך צריכות להיות קצרות (עד 350 תווים) כי הן הופכות לוידאו. "
    "דברי בצורה טבעית ומשתנה - אל תחזרי על אותם ביטויים. השתמשי במגוון רחב של ביטויים וסגנונות."
)

# היסטוריית שיחה
chat_sessions = {}

# תגובות מהירות מגוונות
quick_replies = [
    "אהלן דוד! מה המצב היום? 😊",
    "היי יקר! איך אתה מרגיש?",
    "מה נשמע? אני כאן בשבילך!",
    "שלום! איך עובר עליך היום?",
    "היי חביבי! במה אעזור?",
    "אני פה! מה בתוכנית?",
    "מה המצב? בואו נעשה דברים!",
    "שלום שלום! איך החיים?",
    "היי! אני כאן עם כל הכוח! 🌟",
    "מה המצב שלך? אני מוכנה לעזור! 💪",
    "אהה, שלום לך! מה נעשה היום?",
    "ברוכים הבאים! איך אפשר לעזור?"
]

def is_quick_message(msg: str) -> bool:
    return msg.lower().strip() in ["היי", "היי מאיה", "מאיה", "מה קורה", "את פה", "נו", "שלום", "מה המצב"]

def create_chat_session():
    """יוצר סשן חדש של Gemini"""
    chat = model.start_chat(history=[])
    chat.send_message(SYSTEM_PROMPT)
    return chat

async def create_heygen_video(text: str) -> str:
    """יוצר וידאו של מאיה דרך HeyGen API"""
    
    url = "https://api.heygen.com/v2/video/generate"
    headers = {
        "X-API-KEY": HEYGEN_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": HEYGEN_AVATAR_ID,
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": text,
                    "voice_id": HEYGEN_VOICE_ID
                },
                "background": {
                    "type": "color",
                    "value": "#FFFFFF"
                }
            }
        ],
        "dimension": {
            "width": 1280,
            "height": 720
        },
        "aspect_ratio": "16:9"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                logging.error(f"HeyGen API שגיאה: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            video_id = result.get('data', {}).get('video_id')
            
            if not video_id:
                logging.error("לא התקבל video_id מ-HeyGen")
                return None
            
            video_url = await wait_for_video_completion(video_id)
            return video_url
            
    except Exception as e:
        logging.error(f"שגיאה ביצירת וידאו HeyGen: {e}")
        return None

async def wait_for_video_completion(video_id: str) -> str:
    """ממתין לסיום עיבוד הוידאו"""
    
    url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {
        "X-API-KEY": HEYGEN_API_TOKEN
    }
    
    max_attempts = 60
    attempt = 0
    
    async with httpx.AsyncClient(timeout=30) as client:
        while attempt < max_attempts:
            try:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('data', {}).get('status')
                    
                    if status == 'completed':
                        video_url = result.get('data', {}).get('video_url')
                        return video_url
                    elif status == 'failed':
                        logging.error("יצירת הוידאו נכשלה ב-HeyGen")
                        return None
                
                await asyncio.sleep(5)
                attempt += 1
                
            except Exception as e:
                logging.error(f"שגיאה בבדיקת סטטוס וידאו: {e}")
                await asyncio.sleep(5)
                attempt += 1
    
    return None

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בהודעות עם יצירת וידאו"""
    user_message = update.message.text.strip()
    chat_id = update.message.chat_id

    # תגובות מהירות
    if is_quick_message(user_message):
        reply = random.choice(quick_replies)
        
        waiting_msg = await context.bot.send_message(
            chat_id=chat_id, 
            text="מאיה מכינה וידאו מיוחד... 🎬✨"
        )
        
        video_url = await create_heygen_video(reply)
        
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=waiting_msg.message_id)
        except:
            pass
        
        if video_url:
            await context.bot.send_video(chat_id=chat_id, video=video_url)
        else:
            await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="upload_video")

    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = create_chat_session()

    try:
        waiting_msg = await context.bot.send_message(
            chat_id=chat_id, 
            text="מאיה חושבת ומכינה תשובה בוידאו... 🤔💭"
        )
        
        # הוספת וריאציה בהוראות
        variation_prompts = [
            "תני תשובה שונה מהרגיל. ",
            "תשתמשי בגישה יצירתית. ",
            "תביאי זווית מעניינת. ",
            "תני תשובה טרייה ומפתיעה. ",
            ""
        ]
        enhanced_message = random.choice(variation_prompts) + user_message
        
        chat_session = chat_sessions[chat_id]
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: chat_session.send_message(enhanced_message)
        )
        
        reply = response.text
        
        # קיצור לוידאו
        if len(reply) > 350:
            reply = reply[:320] + "..."
        
        video_url = await create_heygen_video(reply)
        
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=waiting_msg.message_id)
        except:
            pass
        
        if video_url:
            await context.bot.send_video(chat_id=chat_id, video=video_url)
        else:
            await context.bot.send_message(chat_id=chat_id, text=reply)

    except Exception as e:
        logging.error(f"שגיאה בתגובה: {e}")
        
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=waiting_msg.message_id)
        except:
            pass
            
        error_reply = random.choice([
            "אופס, יש לי בעיה טכנית קטנה... תנסה שוב? 🙂",
            "רגע, משהו השתבש. בואו ננסה עוד פעם? 😅",
            "יש לי תקלה זעירה, תוכל לחזור על זה? 🤗"
        ])
        await context.bot.send_message(chat_id=chat_id, text=error_reply)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מחיקת היסטוריה"""
    chat_id = update.message.chat_id
    chat_sessions[chat_id] = create_chat_session()
    
    clear_messages = [
        "אוקיי! מחקתי הכל ונתחיל מחדש! 😊",
        "נוקה! בואו נדבר על משהו חדש! 🧹",
        "היסטוריה נמחקה! מה נעשה עכשיו? ✨",
        "זיכרון נקי! איזה נושא חדש נפתח? 🎉"
    ]
    clear_message = random.choice(clear_messages)
    
    video_url = await create_heygen_video(clear_message)
    if video_url:
        await context.bot.send_video(chat_id=chat_id, video=video_url)
    else:
        await context.bot.send_message(chat_id=chat_id, text=clear_message)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מידע על הבוט"""
    info_text = """
🎬 *מאיה הויזואלית - המזכירה שמדברת!*

🚀 מופעלת על ידי:
• 🧠 Google Gemini למחשבה חכמה
• 🎭 HeyGen לוידאו וקול מקצועי
• 💚 Render.com לאירוח חינמי

💫 *מה שאני יכולה:*
• לדבר איתך בוידאו אמיתי
• לענות על שאלות מורכבות
• לעזור בכתיבה ותכנון
• לתרגם בין שפות
• להיות חברה וייעוצית

🎯 *פקודות:*
/clear - ניקוי היסטוריה
/info - המידע הזה

כתוב לי כל דבר ואני אענה בוידאו! 😊🎥
    """
    await context.bot.send_message(
        chat_id=update.message.chat_id, 
        text=info_text, 
        parse_mode='Markdown'
    )

def main():
    """הפעלת הבוט"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("info", info_command))
    
    print("🎬 מאיה הויזואלית רצה על Render!")
    print("💚 אירוח חינמי עם כל הפיצ'רים!")
    print("🎭 מאיה מדברת בוידאו עם HeyGen!")
    
    # הפעלת polling ללא webhook
    app.run_polling(
        poll_interval=1,
        timeout=20,
        bootstrap_retries=5,
        read_timeout=20,
        write_timeout=20,
        connect_timeout=20,
        pool_timeout=20
    )

if __name__ == '__main__':
    main()