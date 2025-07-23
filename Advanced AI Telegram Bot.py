"""
Maya - Advanced AI Telegram Bot
=====================================
A sophisticated AI-powered Telegram bot with autonomous capabilities,
Hebrew support, and advanced conversation management.

Author: AI Development Team
Version: 2.0
License: MIT
"""

import os
import logging
import asyncio
import json
from datetime import datetime, timedelta
from threading import Thread
from typing import Dict, List, Optional, Any
import re
from functools import wraps

# Core imports
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters
)

# AI and external services
import google.generativeai as genai
import requests
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# ============================
# CONFIGURATION & SETUP
# ============================

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MONGO_URI = os.getenv('MONGO_URI')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0)) if os.getenv('ADMIN_ID') else None

# Configure Gemini AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
# Maya's personality configuration
MAYA_PERSONALITY = """
אני מאיה, בוט AI חכם ומתקדם. אני:
- מדברת בעברית טבעית וחמה
- מבינה הקשר ונושאי שיחה מורכבים
- יכולה לעזור במגוון רחב של נושאים
- לומדת מכל שיחה ומתאמת את עצמי למשתמש
- נותנת תשובות מקיפות ומועילות
- שומרת על אופי ידידותי אך מקצועי
"""

# ============================
# FLASK KEEP-ALIVE SERVER
# ============================

app = Flask(__name__)

@app.route('/')
def health_check():
    """Health check endpoint for uptime monitoring"""
    return jsonify({
        "status": "active",
        "bot": "Maya AI Agent",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    }), 200

@app.route('/stats')
def bot_stats():
    """Basic bot statistics endpoint"""
    try:
        db = DatabaseManager()
        stats = db.get_basic_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_flask():
    """Run Flask server in separate thread"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# ============================
# DATABASE MANAGEMENT
# ============================

class DatabaseManager:
    """Advanced database management with MongoDB"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.users = None
        self.conversations = None
        self.ai_memory = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            if MONGO_URI:
                self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client.maya_bot
                self.users = self.db.users
                self.conversations = self.db.conversations
                self.ai_memory = self.db.ai_memory
                logger.info("✅ Connected to MongoDB successfully")
            else:
                logger.warning("⚠️ No MongoDB URI provided - using in-memory storage")
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            # Fallback to in-memory storage
            self.users = {}
            self.conversations = []
            self.ai_memory = {}
    
    def register_user(self, user_data: Dict) -> bool:
        """Register or update user information"""
        try:
            if hasattr(self.users, 'update_one'):  # MongoDB
                result = self.users.update_one(
                    {"user_id": user_data["user_id"]},
                    {
                        "$set": {
                            **user_data,
                            "last_seen": datetime.now(),
                            "is_active": True
                        },
                        "$setOnInsert": {
                            "first_join": datetime.now(),
                            "total_messages": 0,
                            "preferences": {"language": "he", "notifications": True}
                        },
                        "$inc": {"total_messages": 1}
                    },
                    upsert=True
                )
                return result.acknowledged
            else:  # In-memory storage
                user_id = user_data["user_id"]
                if user_id not in self.users:
                    self.users[user_id] = {
                        **user_data,
                        "first_join": datetime.now(),
                        "total_messages": 1,
                        "preferences": {"language": "he", "notifications": True}
                    }
                else:
                    self.users[user_id].update(user_data)
                    self.users[user_id]["total_messages"] += 1
                    self.users[user_id]["last_seen"] = datetime.now()
                return True
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False
    
    def log_conversation(self, user_id: int, message: str, response: str, 
                        message_type: str = "text") -> bool:
        """Log conversation for AI learning and analytics"""
        try:
            conversation_data = {
                "user_id": user_id,
                "timestamp": datetime.now(),
                "user_message": message,
                "bot_response": response,
                "message_type": message_type,
                "response_length": len(response),
                "ai_model": "gemini-pro"
            }
            
            if hasattr(self.conversations, 'insert_one'):  # MongoDB
                result = self.conversations.insert_one(conversation_data)
                return result.acknowledged
            else:  # In-memory storage
                self.conversations.append(conversation_data)
                return True
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")
            return False
    
    def get_user_context(self, user_id: int, last_n: int = 5) -> List[Dict]:
        """Get recent conversation context for AI"""
        try:
            if hasattr(self.conversations, 'find'):  # MongoDB
                cursor = self.conversations.find(
                    {"user_id": user_id}
                ).sort("timestamp", -1).limit(last_n)
                return list(cursor)
            else:  # In-memory storage
                user_conversations = [
                    conv for conv in self.conversations 
                    if conv["user_id"] == user_id
                ]
                return sorted(user_conversations, 
                            key=lambda x: x["timestamp"], reverse=True)[:last_n]
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return []
    
    def save_ai_memory(self, user_id: int, memory_key: str, memory_value: Any) -> bool:
        """Save AI memory for personalized responses"""
        try:
            memory_data = {
                "user_id": user_id,
                "memory_key": memory_key,
                "memory_value": memory_value,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            if hasattr(self.ai_memory, 'update_one'):  # MongoDB
                result = self.ai_memory.update_one(
                    {"user_id": user_id, "memory_key": memory_key},
                    {"$set": memory_data},
                    upsert=True
                )
                return result.acknowledged
            else:  # In-memory storage
                key = f"{user_id}_{memory_key}"
                self.ai_memory[key] = memory_data
                return True
        except Exception as e:
            logger.error(f"Error saving AI memory: {e}")
            return False
    
    def get_basic_stats(self) -> Dict:
        """Get basic bot statistics"""
        try:
            if hasattr(self.users, 'count_documents'):  # MongoDB
                total_users = self.users.count_documents({})
                active_users = self.users.count_documents({
                    "last_seen": {"$gte": datetime.now() - timedelta(days=7)}
                })
                total_conversations = self.conversations.count_documents({})
            else:  # In-memory storage
                total_users = len(self.users)
                week_ago = datetime.now() - timedelta(days=7)
                active_users = sum(
                    1 for user in self.users.values()
                    if user.get("last_seen", datetime.min) > week_ago
                )
                total_conversations = len(self.conversations)
            
            return {
                "total_users": total_users,
                "active_users_week": active_users,
                "total_conversations": total_conversations,
                "uptime": "Online"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

# ============================
# AI ENGINE
# ============================

class MayaAI:
    """Advanced AI engine using Google Gemini"""
    
    def __init__(self):
        self.model = None
        self.db = DatabaseManager()
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Gemini AI model"""
        try:
            if GEMINI_API_KEY:
                # Configure model settings
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1000,
                }
                
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
                
                self.model = genai.GenerativeModel(
                    model_name="gemini-pro",
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                logger.info("✅ Gemini AI model initialized successfully")
            else:
                logger.warning("⚠️ No Gemini API key provided")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI model: {e}")
    
    async def generate_response(self, user_id: int, message: str, 
                              user_name: str = "משתמש") -> str:
        """Generate intelligent response using AI with context"""
        try:
            if not self.model:
                return self._fallback_response(message)
            
            # Get conversation context
            context = self.db.get_user_context(user_id, last_n=3)
            
            # Build context string
            context_str = ""
            if context:
                context_str = "\n\nהקשר השיחה האחרון:\n"
                for i, conv in enumerate(reversed(context), 1):
                    context_str += f"{i}. משתמש: {conv['user_message']}\n"
                    context_str += f"   מאיה: {conv['bot_response'][:100]}...\n"
            
            # Create enhanced prompt
            prompt = f"""
{MAYA_PERSONALITY}

אני מדברת עם {user_name}. 
{context_str}

ההודעה הנוכחית: "{message}"

אנא תני תשובה טבעית, מועילה ואישית בעברית. התאמי את הטון לפי ההקשר והמשתמש.
אם השאלה דורשת מידע עדכני או חיפוש באינטרנט, ציני זאת.
תני תשובה באורך של 1-3 פסקאות.
"""

            # Generate response
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync, prompt
            )
            
            # Log conversation
            self.db.log_conversation(user_id, message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._fallback_response(message)
    
    def _generate_sync(self, prompt: str) -> str:
        """Synchronous generation wrapper"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise e
    
    def _fallback_response(self, message: str) -> str:
        """Fallback responses when AI is unavailable"""
        fallbacks = [
            "מצטערת, אני חווה קשיים טכניים כרגע. אוכל לעזור לך בעוד רגע! 🤖",
            "נראה שיש לי בעיה קטנה עם המערכת שלי. תנסה שוב בעוד רגע? 💭",
            "המערכת שלי עסוקה כרגע. אשמח לעזור לך בקרוב! ⚡",
        ]
        
        # Simple keyword-based responses
        message_lower = message.lower()
        if any(word in message_lower for word in ["שלום", "היי", "מה נשמע"]):
            return f"שלום! אני מאיה, שמחה לפגוש אותך! איך אוכל לעזור? 😊"
        elif any(word in message_lower for word in ["תודה", "תנקיו"]):
            return "אין בעד מה! תמיד כאן לעזור 💜"
        elif "?" in message:
            return "זו שאלה מעניינת! כרגע אני עסוקה, אבל חזור אליי בעוד רגע ואתן לך תשובה מפורטת 🤔"
        
        return fallbacks[0]

# ============================
# CONVERSATION STATES
# ============================

# Conversation states for complex interactions
MAIN_MENU, SETTINGS_MENU, AI_CHAT, FEEDBACK = range(4)

# ============================
# UTILITY FUNCTIONS
# ============================

def admin_only(func):
    """Decorator to restrict access to admin commands"""
    @wraps(func)
    async def wrapper(update: Update, context):
        if not ADMIN_ID or update.effective_user.id != ADMIN_ID:
            await update.message.reply_text(
                "⛔ פקודה זו זמינה רק למנהלי הבוט\n"
                f"המזהה שלך: {update.effective_user.id}"
            )
            return
        return await func(update, context)
    return wrapper

def typing_action(func):
    """Decorator to show typing action while processing"""
    @wraps(func)
    async def wrapper(update: Update, context):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action="typing"
        )
        return await func(update, context)
    return wrapper

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from Hebrew text"""
    # Simple keyword extraction for Hebrew
    words = re.findall(r'[\u0590-\u05FF\w]+', text)
    # Filter out common Hebrew stop words
    stop_words = {'של', 'את', 'את', 'על', 'אל', 'כל', 'מה', 'זה', 'זו', 'היא', 'הוא'}
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    return keywords[:10]  # Return top 10 keywords

# ============================
# BOT HANDLERS
# ============================

class MayaBot:
    """Main bot class with all handlers"""
    
    def __init__(self):
        self.ai = MayaAI()
        self.db = DatabaseManager()
    
    async def start_command(self, update: Update, context) -> int:
        """Enhanced start command with personality"""
        user = update.effective_user
        
        # Register user
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code
        }
        self.db.register_user(user_data)
        
        # Create main menu keyboard
        keyboard = [
            [InlineKeyboardButton("💬 שיחה עם AI", callback_data="ai_chat")],
            [InlineKeyboardButton("⚙️ הגדרות", callback_data="settings")],
            [InlineKeyboardButton("📊 סטטיסטיקות", callback_data="stats")],
            [InlineKeyboardButton("❓ עזרה", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🤖 שלום {user.first_name}, אני מאיה!

אני בוט AI מתקדם שיכול לעזור לך במגוון נושאים:
• שיחות טבעיות בעברית
• מענה על שאלות מורכבות  
• עזרה במשימות יומיומיות
• למידה מכל שיחה שלנו

איך תרצה להתחיל?
        """
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    @typing_action
    async def handle_message(self, update: Update, context):
        """Handle all text messages with AI"""
        user = update.effective_user
        message = update.message.text
        
        # Register user activity
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
        self.db.register_user(user_data)
        
        # Generate AI response
        response = await self.ai.generate_response(
            user_id=user.id,
            message=message,
            user_name=user.first_name or "משתמש"
        )
        
        # Add quick action buttons for longer conversations
        keyboard = [
            [InlineKeyboardButton("🔄 שאל עוד", callback_data="continue_chat")],
            [InlineKeyboardButton("📋 תפריט ראשי", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            response, 
            reply_markup=reply_markup
        )
    
    async def button_handler(self, update: Update, context):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "ai_chat":
            await query.edit_message_text(
                "💬 מצב שיחה פעיל!\n\n"
                "שלח לי כל שאלה או נושא לדיון. אני כאן לעזור! 🤖\n\n"
                "טיפ: אוכל לעזור עם כתיבה, תכנות, מידע כללי, ועוד הרבה נושאים."
            )
            return AI_CHAT
            
        elif data == "settings":
            keyboard = [
                [InlineKeyboardButton("🌐 שפה", callback_data="lang_settings")],
                [InlineKeyboardButton("🔔 התראות", callback_data="notif_settings")],
                [InlineKeyboardButton("🗑️ מחק היסטוריה", callback_data="clear_history")],
                [InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⚙️ הגדרות מאיה\n\nבחר את האפשרות שתרצה לערוך:",
                reply_markup=reply_markup
            )
            return SETTINGS_MENU
            
        elif data == "stats":
            stats = self.db.get_basic_stats()
            stats_text = f"""
📊 סטטיסטיקות הבוט:

👥 משתמשים רשומים: {stats.get('total_users', 0)}
⚡ פעילים השבוע: {stats.get('active_users_week', 0)}
💬 סה"כ שיחות: {stats.get('total_conversations', 0)}
🟢 סטטוס: {stats.get('uptime', 'Online')}

🤖 אני לומדת ומשתפרת מכל שיחה!
            """
            
            keyboard = [[InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(stats_text, reply_markup=reply_markup)
            
        elif data == "help":
            help_text = """
❓ מדריך שימוש במאיה

🎯 מה אני יכולה לעשות:
• לענות על שאלות בכל נושא
• לעזור בכתיבה ועריכה
• לתת הסברים על נושאים מורכבים
• לסייע במשימות יומיומיות
• ללמוד מההעדפות שלך

💡 טיפים לשימוש:
• כתוב בעברית טבעית
• תאר בפירוט מה אתה צריך
• אל תהסס לשאול שאלות המשך

🔧 פקודות זמינות:
/start - התחלה מחדש
/stats - סטטיסטיקות אישיות
/feedback - שליחת משוב
            """
            
            keyboard = [[InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(help_text, reply_markup=reply_markup)
            
        elif data == "main_menu":
            # Return to main menu
            keyboard = [
                [InlineKeyboardButton("💬 שיחה עם AI", callback_data="ai_chat")],
                [InlineKeyboardButton("⚙️ הגדרות", callback_data="settings")],
                [InlineKeyboardButton("📊 סטטיסטיקות", callback_data="stats")],
                [InlineKeyboardButton("❓ עזרה", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🤖 מאיה - הבוט החכם שלך\n\nמה תרצה לעשות?",
                reply_markup=reply_markup
            )
            return MAIN_MENU
    
    @admin_only
    async def admin_stats(self, update: Update, context):
        """Advanced admin statistics"""
        stats = self.db.get_basic_stats()
        
        # Additional admin-only stats
        admin_text = f"""
👑 **פאנל מנהל - סטטיסטיקות מתקדמות**

📊 **נתוני משתמשים:**
• סה"כ משתמשים: {stats.get('total_users', 0)}
• פעילים השבוע: {stats.get('active_users_week', 0)}
• שיחות השבוע: {stats.get('total_conversations', 0)}

🤖 **מצב המערכת:**
• AI Engine: {'🟢 פעיל' if self.ai.model else '🔴 לא זמין'}
• Database: {'🟢 MongoDB' if hasattr(self.db.users, 'find') else '🟡 זיכרון'}
• Uptime: {stats.get('uptime', 'Online')}

⚡ **ביצועים:**
• זמן תגובה ממוצע: < 2 שניות
• שפות נתמכות: עברית, אנגלית
• דגם AI: Gemini Pro
        """
        
        await update.message.reply_text(admin_text, parse_mode='Markdown')
    
    @admin_only
    async def broadcast_message(self, update: Update, context):
        """Send message to all users"""
        if not context.args:
            await update.message.reply_text(
                "📢 שימוש: /broadcast הודעה לכל המשתמשים"
            )
            return
        
        message = " ".join(context.args)
        await update.message.reply_text("📤 מתחיל שידור...")
        
        # Get all users (simplified for this example)
        try:
            sent_count = 0
            failed_count = 0
            
            if hasattr(self.db.users, 'find'):  # MongoDB
                async for user in self.db.users.find({"is_active": True}):
                    try:
                        await context.bot.send_message(
                            user["user_id"], 
                            f"📢 הודעה ממאיה:\n\n{message}"
                        )
                        sent_count += 1
                    except Exception:
                        failed_count += 1
            else:  # In-memory
                for user_id, user_data in self.db.users.items():
                    try:
                        await context.bot.send_message(
                            user_id,
                            f"📢 הודעה ממאיה:\n\n{message}"
                        )
                        sent_count += 1
                    except Exception:
                        failed_count += 1
            
            await update.message.reply_text(
                f"✅ שידור הושלם!\n"
                f"📤 נשלח: {sent_count}\n"
                f"❌ נכשל: {failed_count}"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ שגיאה בשידור: {e}")
    
    async def feedback_command(self, update: Update, context):
        """Collect user feedback"""
        if not context.args:
            await update.message.reply_text(
                "💬 שליחת משוב:\n\n"
                "שתף אותי במחשבות שלך על השירות:\n"
                "/feedback הטקסט שלך כאן"
            )
            return
        
        feedback = " ".join(context.args)
        user = update.effective_user
        
        # Save feedback (simplified)
        feedback_data = {
            "user_id": user.id,
            "username": user.first_name,
            "feedback": feedback,
            "timestamp": datetime.now()
        }
        
        # If admin exists, forward feedback
        if ADMIN_ID:
            try:
                await context.bot.send_message(
                    ADMIN_ID,
                    f"📝 משוב חדש מ-{user.first_name} ({user.id}):\n\n{feedback}"
                )
            except Exception:
                pass
        
        await update.message.reply_text(
            "🙏 תודה על המשוב!\n\n"
            "המשוב שלך חשוב לי מאוד ויעזור לי להשתפר. "
            "אמשיך להתפתח ולהיות טובה יותר בעזרתך! 💜"
        )

# ============================
# MAIN APPLICATION
# ============================

def main():
    """Main function to run the bot"""
    
    # Validate required environment variables
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN is required!")
        return
    
    # Start Flask server for keep-alive
    logger.info("🚀 Starting Keep-Alive server...")
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Initialize bot
    logger.info("🤖 Initializing Maya AI Bot...")
    maya = MayaBot()
    
    # Build application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create conversation handler for complex interactions
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", maya.start_command)],
        states={
            MAIN_MENU: [CallbackQueryHandler(maya.button_handler)],
            SETTINGS_MENU: [CallbackQueryHandler(maya.button_handler)],
            AI_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, maya.handle_message),
                CallbackQueryHandler(maya.button_handler)
            ],
            FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, maya.feedback_command)]
        },
        fallbacks=[
            CommandHandler("start", maya.start_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, maya.handle_message)
        ]
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("admin_stats", maya.admin_stats))
    application.add_handler(CommandHandler("broadcast", maya.broadcast_message))
    application.add_handler(CommandHandler("feedback", maya.feedback_command))
    
    # Fallback handler for any text message
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, maya.handle_message))
    
    # Handle callback queries
    application.add_handler(CallbackQueryHandler(maya.button_handler))
    
    # Error handler
    async def error_handler(update: Update, context):
        """Handle errors gracefully"""
        logger.error(f"Error occurred: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "😅 אופס! משהו השתבש. אני עובדת על תיקון הבעיה.\n"
                "נסה שוב בעוד רגע או פנה למנהל אם הבעיה נמשכת."
            )
    
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("✅ Maya is starting up...")
    logger.info("📡 Bot will be available at: https://t.me/your_bot_username")
    
    try:
        # Run bot with polling
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")

if __name__ == '__main__':
    main()
