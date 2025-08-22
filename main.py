#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maya AI Agent - Telegram Bot with Gemini Integration
==================================================
A focused implementation of Maya AI Telegram bot that provides:
- Complete Telegram bot connection
- Enhanced error handling in Hebrew
- Gemini AI integration for smart responses
- Environment variable verification
- Clear logging and user-friendly messages

Requirements addressed from problem statement:
- הוסף קובץ main.py לפרויקט maya-ai-agent שמבצע חיבור מלא לבוט טלגרם
- ממש טיפול משופר בשגיאות
- כל הודעה מהמשתמש תעבור ל-Gemini API
- הבוט יחזיר תשובה חכמה, עם טיפול בשגיאות בעברית
- ודא שכל משתני הסביבה נבדקים
- השתמש ב-Application של python-telegram-bot ובדוגמת קוד עם async
"""

import os
import logging
import asyncio
from typing import Optional
from datetime import datetime

# Telegram Bot imports
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Gemini AI imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Warning: google-generativeai not installed. Using demo responses.")

# ============================
# CONFIGURATION & SETUP
# ============================

# Configure logging with Hebrew support
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# Environment variables validation
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
ADMIN_ID = os.getenv('ADMIN_ID')

def validate_environment() -> bool:
    """
    בדיקת משתני סביבה נדרשים
    Validate required environment variables
    """
    missing_vars = []
    
    if not BOT_TOKEN:
        missing_vars.append('TELEGRAM_BOT_TOKEN')
    
    if not GEMINI_API_KEY:
        missing_vars.append('GEMINI_API_KEY')
    
    if missing_vars:
        error_msg = f"❌ חסרים משתני סביבה נדרשים: {', '.join(missing_vars)}"
        logger.error(error_msg)
        print(error_msg)
        print("\n📋 הגדר את המשתנים הבאים:")
        for var in missing_vars:
            print(f"   export {var}='your_value_here'")
        print("\n💡 עצה: צור קובץ .env עם המשתנים הנדרשים")
        return False
    
    logger.info("✅ כל משתני הסביבה מוגדרים כראוי")
    return True

# Initialize Gemini AI if available
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Configure model for better Hebrew support
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1000,
        }
        
        # Safety settings
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        model = genai.GenerativeModel(
            model_name="gemini-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        logger.info("✅ Gemini AI מאותחל בהצלחה")
        
    except Exception as e:
        logger.error(f"❌ שגיאה באתחול Gemini AI: {e}")
        model = None
else:
    model = None
    if not GEMINI_AVAILABLE:
        logger.warning("⚠️ Gemini AI לא זמין - משתמש בתגובות דמו")
    elif not GEMINI_API_KEY:
        logger.warning("⚠️ מפתח Gemini API לא סופק")

# ============================
# AI RESPONSE GENERATION
# ============================

async def generate_ai_response(user_message: str, user_name: str = "משתמש") -> str:
    """
    יצירת תגובה חכמה באמצעות Gemini AI
    Generate smart response using Gemini AI with error handling
    """
    try:
        if model and GEMINI_AVAILABLE:
            # Create context-aware prompt in Hebrew
            prompt = f"""
אתה מאיה, בוט AI חכם ומועיל שמדבר עברית טבעית וחמה.

המשתמש {user_name} שלח לך את ההודעה הבאה: "{user_message}"

אנא השב בעברית בצורה:
- טבעית וידידותית
- מועילה ומידעית
- קצרה ולעניין (לא יותר מ-200 מילים)
- עם אמוג'ים רלוונטיים

אם המשתמש שואל על דברים שאינך יודע או לא יכול לעזור בהם, הסבר בנחמה ובצע הצעות חלופיות.
"""
            
            # Generate response
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                logger.info(f"✅ תגובת AI נוצרה בהצלחה עבור: {user_name}")
                return response.text.strip()
            else:
                logger.warning("⚠️ Gemini AI החזיר תגובה ריקה")
                return "מצטערת, לא הצלחתי לחשוב על תשובה טובה כרגע. תוכל לנסח את השאלה שוב? 🤔"
                
        else:
            # Demo response when Gemini is not available
            demo_responses = [
                f"שלום {user_name}! 👋 קיבלתי את ההודעה שלך: '{user_message}'\n\n"
                "זוהי תגובת דמו כיוון ש-Gemini AI לא מוגדר. אני אוכל לעזור לך טוב יותר עם מפתח API תקין! 🤖",
                
                f"היי {user_name}! 😊 ראיתי שכתבת: '{user_message}'\n\n"
                "אני בשלב פיתוח וצריכה מפתח Gemini API כדי לתת לך תשובות חכמות! 🧠✨",
                
                f"תודה על ההודעה {user_name}! 📝\n\n"
                "כרגע אני עובדת במצב דמו. עם מפתח Gemini API אני אוכל לעזור לך הרבה יותר! 🚀"
            ]
            
            import random
            return random.choice(demo_responses)
            
    except Exception as e:
        logger.error(f"❌ שגיאה ביצירת תגובת AI: {e}")
        return (
            f"😅 אופס! קרתה שגיאה בזמן שחשבתי על תשובה.\n\n"
            f"🔧 פרטי השגיאה: {str(e)[:100]}...\n\n"
            "נסה שוב בעוד רגע, או פנה למנהל אם הבעיה נמשכת. 💭"
        )

# ============================
# TELEGRAM BOT HANDLERS
# ============================

async def start_command(update: Update, context) -> None:
    """
    פקודת התחלה של הבוט
    Bot start command handler
    """
    user = update.effective_user
    user_name = user.first_name if user.first_name else "משתמש"
    
    welcome_message = f"""
🤖 שלום {user_name}, אני מאיה!

אני בוט AI מתקדם שיכול לעזור לך במגוון נושאים:
• מענה לשאלות בעברית 💬
• מידע ועצות 💡
• עזרה בכתיבה ויצירתיות ✍️
• שיחה טבעית וידידותית 😊

פשוט שלח לי הודעה ואני אענה לך! 

🎯 דוגמאות למה שתוכל לשאול:
• "מה מזג האויר?"
• "עזור לי לכתוב אימייל"
• "ספר לי בדיחה"
• "איך אני יכול לשפר את הבריאות שלי?"

בואו נתחיל! 🚀
"""
    
    try:
        await update.message.reply_text(welcome_message)
        logger.info(f"✅ הודעת ברכה נשלחה ל-{user_name} (ID: {user.id})")
    except Exception as e:
        logger.error(f"❌ שגיאה בשליחת הודעת ברכה: {e}")

async def help_command(update: Update, context) -> None:
    """
    פקודת עזרה
    Help command handler
    """
    help_message = """
📚 **עזרה - איך להשתמש במאיה**

🤖 **על מאיה:**
אני בוט AI שמדבר עברית ויכול לעזור במגוון נושאים.

💬 **איך להשתמש:**
פשוט שלח לי הודעה רגילה והאני אענה!

🎯 **דוגמאות:**
• שאלות כלליות: "מה זה בינה מלאכותית?"
• עצות: "איך לשפר את הריכוז?"
• יצירתיות: "כתוב לי שיר קצר"
• עזרה בכתיבה: "עזור לי לנסח מייל למנהל"

⚡ **פקודות זמינות:**
/start - התחלה מחדש
/help - עזרה זו

🔧 **בעיות?**
אם יש בעיה, פנה למנהל או נסה שוב בעוד רגע.

בהצלחה! 🌟
"""
    
    try:
        await update.message.reply_text(help_message, parse_mode='Markdown')
        logger.info(f"✅ הודעת עזרה נשלחה ל-{update.effective_user.first_name}")
    except Exception as e:
        logger.error(f"❌ שגיאה בשליחת הודעת עזרה: {e}")

async def handle_message(update: Update, context) -> None:
    """
    טיפול בהודעות טקסט מהמשתמש
    Handle all text messages from users
    """
    user = update.effective_user
    user_name = user.first_name if user.first_name else "משתמש"
    message_text = update.message.text
    
    # Log incoming message
    logger.info(f"📨 הודעה מ-{user_name} (ID: {user.id}): {message_text[:50]}...")
    
    try:
        # Send typing action to show bot is processing
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Generate AI response
        ai_response = await generate_ai_response(message_text, user_name)
        
        # Send response
        await update.message.reply_text(ai_response)
        
        logger.info(f"✅ תגובה נשלחה ל-{user_name}")
        
    except Exception as e:
        logger.error(f"❌ שגיאה בטיפול בהודעה מ-{user_name}: {e}")
        
        # Send user-friendly error message in Hebrew
        error_message = (
            "😅 אופס! משהו השתבש בעיבוד ההודעה שלך.\n\n"
            "🔄 אנא נסה שוב בעוד רגע.\n\n"
            f"🔧 אם הבעיה נמשכת, פנה למנהל עם קוד השגיאה: {str(e)[:50]}..."
        )
        
        try:
            await update.message.reply_text(error_message)
        except Exception as send_error:
            logger.error(f"❌ שגיאה גם בשליחת הודעת השגיאה: {send_error}")

async def error_handler(update: Update, context) -> None:
    """
    טיפול בשגיאות כלליות של הבוט
    General error handler for the bot
    """
    logger.error(f"❌ שגיאה כללית בבוט: {context.error}")
    logger.error(f"Update שגרם לשגיאה: {update}")
    
    # Try to send error message to user if possible
    if update and update.effective_message:
        try:
            error_message = (
                "😅 אופס! קרתה שגיאה לא צפויה.\n\n"
                "🔄 אנא נסה שוב בעוד כמה רגעים.\n\n"
                "🛠️ אם הבעיה נמשכת, פנה למנהל המערכת."
            )
            await update.effective_message.reply_text(error_message)
        except Exception as e:
            logger.error(f"❌ שגיאה בשליחת הודעת שגיאה למשתמש: {e}")
    
    # Notify admin if configured
    if ADMIN_ID and context.bot:
        try:
            admin_message = (
                f"🚨 **שגיאה במערכת מאיה**\n\n"
                f"**שגיאה:** `{str(context.error)}`\n"
                f"**זמן:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"**Update:** {type(update).__name__ if update else 'None'}"
            )
            await context.bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ שגיאה בהודעה למנהל: {e}")

# ============================
# MAIN APPLICATION
# ============================

def main() -> None:
    """
    פונקציה ראשית להפעלת הבוט
    Main function to run the bot
    """
    print("=" * 60)
    print("🤖 מאיה - בוט AI מתקדם עם Gemini")
    print("Maya - Advanced AI Bot with Gemini Integration")
    print("=" * 60)
    
    # Validate environment variables
    if not validate_environment():
        print("\n❌ הבוט לא יכול להתחיל ללא משתני הסביבה הנדרשים")
        print("🔧 אנא הגדר את משתני הסביבה ונסה שוב")
        return
    
    try:
        # Create application
        print("🔧 יוצר את אפליקציית הבוט...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        print("📋 מוסיף handlers...")
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        print("✅ הבוט הוכן בהצלחה!")
        print(f"🤖 מפתח Gemini AI: {'✅ מוגדר' if GEMINI_API_KEY else '❌ לא מוגדר'}")
        print(f"👤 Admin ID: {'✅ מוגדר' if ADMIN_ID else '⚠️ לא מוגדר'}")
        print("\n🚀 מתחיל את הבוט...")
        print("📡 הבוט יהיה זמין בקרוב...")
        print("🔄 לחץ Ctrl+C כדי לעצור את הבוט")
        print("=" * 60)
        
        # Run the bot
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )
        
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("⏹️ הבוט נעצר על ידי המשתמש")
        print("👋 תודה שהשתמשת במאיה!")
        print("=" * 60)
    except Exception as e:
        logger.error(f"❌ שגיאה קריטית בהפעלת הבוט: {e}")
        print(f"\n❌ שגיאה קריטית: {e}")
        print("🔧 אנא בדוק את ההגדרות ונסה שוב")

if __name__ == '__main__':
    main()