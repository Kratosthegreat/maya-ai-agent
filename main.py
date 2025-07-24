async def button_handler(self, update: Update, context):
        """Handle inline keyboard callbacks with task management"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "ai_chat":
            await query.edit_message_text(
                "💬 **מצב שיחה פעיל!**\n\n"
                "שלח לי כל שאלה או נושא לדיון. אני כאן לעזור! 🤖\n\n"
                "**💡 דוגמאות למה שאני יכולה לעזור:**\n"
                "• תזכורות ומשימות: \"תזכור לי"""
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
import uuid

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
# TASK MANAGEMENT SYSTEM
# ============================

class TaskManager:
    """Smart task management with AI integration"""
    
    def __init__(self, db):
        self.db = db
    
    def analyze_user_intent(self, message: str) -> Optional[tuple]:
        """Analyze user intent with confidence scoring"""
        task_patterns = {
            'reminder': ['תזכור', 'תזכיר', 'אל תשכח', 'reminder', 'תזכורת'],
            'meeting': ['פגישה', 'ישיבה', 'מפגש', 'meeting', 'פגש'],
            'schedule': ['תזמן', 'קבע', 'לוח זמנים', 'schedule', 'ארגן'],
            'email': ['אימייל', 'מייל', 'שלח הודעה', 'email', 'כתוב'],
            'research': ['חפש', 'מצא', 'מחקר', 'research', 'בדוק'],
            'call': ['תתקשר', 'שיחה', 'טלפון', 'call', 'חייג'],
            'document': ['מסמך', 'דוח', 'כתוב', 'document', 'הכן']
        }
        
        confidence_scores = {}
        message_lower = message.lower()
        
        for intent, keywords in task_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                confidence_scores[intent] = score
        
        return max(confidence_scores.items(), key=lambda x: x[1]) if confidence_scores else None
    
    def extract_task_details(self, message: str) -> Dict:
        """Extract task details from message"""
        intent_result = self.analyze_user_intent(message)
        intent = intent_result[0] if intent_result else 'other'
        
        # Extract priority
        priority_keywords = {
            'urgent': ['דחוף', 'מיידי', 'חירום', 'urgent'],
            'high': ['חשוב', 'priority', 'גבוה'],
            'low': ['לא דחוף', 'כשיהיה זמן', 'low']
        }
        
        priority = 'medium'  # default
        message_lower = message.lower()
        
        for level, keywords in priority_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                priority = level
                break
        
        # Extract due date
        due_date = self._extract_due_date(message)
        
        # Generate title
        title = message[:50] + "..." if len(message) > 50 else message
        
        return {
            'title': title,
            'description': message,
            'category': intent,
            'priority': priority,
            'due_date': due_date,
            'status': 'pending'
        }
    
    def _extract_due_date(self, message: str) -> Optional[str]:
        """Extract due date from natural language"""
        from datetime import datetime, timedelta
        
        message_lower = message.lower()
        today = datetime.now()
        
        if any(word in message_lower for word in ['היום', 'today']):
            return today.isoformat()
        elif any(word in message_lower for word in ['מחר', 'tomorrow']):
            return (today + timedelta(days=1)).isoformat()
        elif any(word in message_lower for word in ['השבוע', 'this week']):
            return (today + timedelta(days=7)).isoformat()
        elif any(word in message_lower for word in ['השבוע הבא', 'next week']):
            return (today + timedelta(days=14)).isoformat()
        elif any(word in message_lower for word in ['החודש', 'this month']):
            return (today + timedelta(days=30)).isoformat()
        
        return None
    
    async def create_task_from_message(self, user_id: int, message: str) -> Optional[str]:
        """Create task automatically from user message"""
        intent_result = self.analyze_user_intent(message)
        
        if not intent_result:
            return None
        
        intent, confidence = intent_result
        
        # Only create task for high-confidence task-related intents
        if confidence >= 1 and intent in ['reminder', 'meeting', 'schedule']:
            task_details = self.extract_task_details(message)
            task_details['user_id'] = user_id
            task_details['created_by_ai'] = True
            
            # Save task (simplified for in-memory storage)
            task_id = self._save_task(task_details)
            
            priority_emoji = {'urgent': '🔥', 'high': '⚡', 'medium': '📋', 'low': '📝'}
            category_emoji = {
                'reminder': '⏰', 'meeting': '🤝', 'schedule': '📅', 
                'email': '📧', 'research': '🔍', 'call': '📞', 'document': '📄'
            }
            
            response = f"""✅ יצרתי עבורך משימה חדשה!

{category_emoji.get(intent, '📋')} **{task_details['title']}**
{priority_emoji.get(task_details['priority'], '📋')} עדיפות: {task_details['priority']}"""
            
            if task_details['due_date']:
                due_date = datetime.fromisoformat(task_details['due_date'])
                response += f"\n📅 תאריך יעד: {due_date.strftime('%d/%m/%Y')}"
            
            response += f"\n\nהשתמש ב-/tasks כדי לראות את כל המשימות שלך"
            
            return response
        
        return None
    
    def _save_task(self, task_details: Dict) -> str:
        """Save task to storage (simplified)"""
        import uuid
        task_id = str(uuid.uuid4())
        task_details['id'] = task_id
        task_details['created_at'] = datetime.now().isoformat()
        
        # Save to database or in-memory storage
        if hasattr(self.db, 'tasks'):
            if not hasattr(self.db, 'tasks'):
                self.db.tasks = {}
            self.db.tasks[task_id] = task_details
        
        return task_id

# ============================
# AI ENGINE WITH SMART FEATURES
# ============================

class MayaAI:
    """Advanced AI engine with task management and smart responses"""
    
    def __init__(self):
        self.model = None
        self.db = DatabaseManager()
        self.task_manager = TaskManager(self.db)
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
    
    async def build_rich_context(self, user_id: int, message: str, intent=None) -> str:
        """Build comprehensive context for AI response"""
        # Get conversation history
        context = self.db.get_user_context(user_id, last_n=3)
        
        # Get user tasks (if any)
        user_tasks = getattr(self.db, 'tasks', {})
        user_task_list = [task for task in user_tasks.values() if task.get('user_id') == user_id]
        
        # Build context string
        context_str = ""
        if context:
            context_str = "\n\nהיסטוריית השיחה האחרונה:\n"
            for i, conv in enumerate(reversed(context), 1):
                context_str += f"{i}. משתמש: {conv['user_message']}\n"
                context_str += f"   מאיה: {conv['bot_response'][:100]}...\n"
        
        # Add tasks context
        tasks_str = ""
        if user_task_list:
            pending_tasks = [t for t in user_task_list if t.get('status') == 'pending']
            if pending_tasks:
                tasks_str = f"\n\nמשימות פתוחות של המשתמש ({len(pending_tasks)}):\n"
                for task in pending_tasks[-3:]:  # Show last 3 tasks
                    tasks_str += f"• {task['title']} ({task['category']})\n"
        
        # Intent context
        intent_str = ""
        if intent:
            intent_str = f"\n\nכוונה מזוהה: {intent[0]} (ביטחון: {intent[1]})"
        
        return f"""
{MAYA_PERSONALITY}

כמזכירה אישית חכמה, אתה יכולה לעזור עם:
- יצירת תזכורות ומשימות
- ארגון פגישות ולוח זמנים  
- מחקר וחיפוש מידע
- כתיבת אימיילים ומסמכים
- ניהול משימות יומיומיות

{context_str}{tasks_str}{intent_str}

ההודעה הנוכחית: "{message}"

הגב בעברית טבעית וידידותית. אם המשתמש מבקש משימה או תזכורת, הציעי ליצור אותה עבורו.
התייחסי להיסטוריה ולמשימות הקיימות אם רלוונטי.
"""
    
    async def generate_response(self, user_id: int, message: str, 
                              user_name: str = "משתמש") -> str:
        """Generate intelligent response with task management"""
        try:
            if not self.model:
                return self._fallback_response(message)
            
            # Analyze user intent
            intent = self.task_manager.analyze_user_intent(message)
            
            # Build rich context
            context = await self.build_rich_context(user_id, message, intent)
            
            # Generate AI response
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync, context
            )
            
            # Check if we should create a task
            task_result = await self.task_manager.create_task_from_message(user_id, message)
            
            if task_result:
                response += f"\n\n{task_result}"
            
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
        """Enhanced fallback responses with task awareness"""
        message_lower = message.lower()
        
        # Task-related fallbacks
        if any(word in message_lower for word in ["תזכור", "פגישה", "משימה"]):
            return "אני מזכירה אישית חכמה! כרגע יש לי בעיה טכנית קטנה, אבל בקרוב אוכל לעזור לך עם משימות ותזכורות! 🗓️"
        
        # Regular fallbacks
        if any(word in message_lower for word in ["שלום", "היי", "מה נשמע"]):
            return f"שלום! אני מאיה, המזכירה האישית החכמה שלך! איך אוכל לעזור? 😊\n\nאני יכולה לעזור עם תזכורות, פגישות, מחקר ועוד!"
        elif any(word in message_lower for word in ["תודה", "תנקיו"]):
            return "אין בעד מה! זה התפקיד שלי לעזור לך! 💜"
        elif "?" in message:
            return "זו שאלה מעניינת! כרגע אני עסוקה, אבל חזור אליי בעוד רגע ואתן לך תשובה מפורטת 🤔"
        
        return "מצטערת, אני חווה קשיים טכניים כרגע. אוכל לעזור לך בעוד רגע! 🤖"

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
        """Handle all text messages with enhanced AI and task management"""
        user = update.effective_user
        message = update.message.text
        
        # Register user activity
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
        self.db.register_user(user_data)
        
        # Send typing indicator for better UX
        await asyncio.sleep(0.5)  # Small delay for natural feeling
        
        # Generate AI response with task management
        response = await self.ai.generate_response(
            user_id=user.id,
            message=message,
            user_name=user.first_name or "משתמש"
        )
        
        # Create smart keyboard based on message content
        keyboard = self._create_smart_keyboard(message, user.id)
        
        await update.message.reply_text(
            response, 
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    def _create_smart_keyboard(self, message: str, user_id: int) -> InlineKeyboardMarkup:
        """Create contextual keyboard based on message content"""
        keyboard = []
        
        # Check if message is task-related
        intent = self.ai.task_manager.analyze_user_intent(message)
        
        if intent and intent[0] in ['reminder', 'meeting', 'schedule']:
            keyboard.append([
                InlineKeyboardButton("📋 המשימות שלי", callback_data="my_tasks"),
                InlineKeyboardButton("➕ משימה חדשה", callback_data="new_task")
            ])
        
        # Always show these options
        keyboard.extend([
            [InlineKeyboardButton("🔄 המשך שיחה", callback_data="continue_chat")],
            [InlineKeyboardButton("📋 תפריט ראשי", callback_data="main_menu")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def tasks_command(self, update: Update, context):
        """Show user tasks with management options"""
        user_id = update.effective_user.id
        
        # Get user tasks
        all_tasks = getattr(self.db, 'tasks', {})
        user_tasks = [task for task in all_tasks.values() if task.get('user_id') == user_id]
        
        if not user_tasks:
            keyboard = [[
                InlineKeyboardButton("➕ צור משימה ראשונה", callback_data="new_task"),
                InlineKeyboardButton("❓ איך זה עובד?", callback_data="tasks_help")
            ]]
            
            await update.message.reply_text(
                "📋 **המשימות שלי**\n\n"
                "אין לך משימות פעילות כרגע.\n"
                "אני יכולה לעזור לך ליצור משימות חדשות!\n\n"
                "💡 פשוט שלח לי הודעה כמו:\n"
                "• \"תזכור לי לקרוא לרופא מחר\"\n"
                "• \"תקבע פגישה עם הצוות השבוע\"\n"
                "• \"תזכיר לי לשלוח דוח עד יום חמישי\"",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Sort tasks by priority and date
        pending_tasks = [t for t in user_tasks if t.get('status') == 'pending']
        completed_tasks = [t for t in user_tasks if t.get('status') == 'completed']
        
        # Create task display
        tasks_text = f"📋 **המשימות שלי** ({len(pending_tasks)} פעילות)\n\n"
        
        # Priority emojis
        priority_emoji = {'urgent': '🔥', 'high': '⚡', 'medium': '📋', 'low': '📝'}
        category_emoji = {
            'reminder': '⏰', 'meeting': '🤝', 'schedule': '📅', 
            'email': '📧', 'research': '🔍', 'call': '📞', 'document': '📄'
        }
        
        # Show pending tasks
        if pending_tasks:
            tasks_text += "**🟡 משימות פעילות:**\n"
            for i, task in enumerate(pending_tasks[:5], 1):
                emoji = category_emoji.get(task.get('category', 'other'), '📋')
                priority = priority_emoji.get(task.get('priority', 'medium'), '📋')
                
                tasks_text += f"{i}. {emoji} {task['title'][:40]}...\n"
                tasks_text += f"   {priority} {task.get('priority', 'medium')} עדיפות"
                
                if task.get('due_date'):
                    try:
                        due_date = datetime.fromisoformat(task['due_date'])
                        tasks_text += f" | 📅 {due_date.strftime('%d/%m')}"
                    except:
                        pass
                
                tasks_text += "\n\n"
        
        # Show completed tasks summary
        if completed_tasks:
            tasks_text += f"**✅ הושלמו:** {len(completed_tasks)} משימות\n\n"
        
        tasks_text += "💡 שלח לי הודעה עם משימה חדשה והיא תתווסף אוטומטית!"
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("➕ משימה חדשה", callback_data="new_task")],
            [InlineKeyboardButton("✅ סמן כהושלם", callback_data="complete_task")],
            [InlineKeyboardButton("🗑️ מחק משימה", callback_data="delete_task")],
            [InlineKeyboardButton("⬅️ חזור לתפריט", callback_data="main_menu")]
        ]
        
        await update.message.reply_text(
            tasks_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def new_task_command(self, update: Update, context):
        """Create new task interactively"""
        help_text = """
➕ **יצירת משימה חדשה**

אני יכולה ליצור עבורך משימות בכמה דרכים:

**🗣️ דרך שיחה טבעית:**
פשוט שלח לי הודעה כמו:
• "תזכור לי לקרוא לרופא מחר בשעה 10"
• "תקבע פגישה עם הצוות השבוע הבא"  
• "תזכיר לי לשלוח דוח עד יום חמישי"

**📝 סוגי משימות שאני מבינה:**
⏰ תזכורות - "תזכור לי..."
🤝 פגישות - "תקבע פגישה..."
📅 תזמון - "תזמן..."
📧 אימיילים - "תשלח אימייל..."
🔍 מחקר - "תבדוק..."
📞 שיחות - "תתקשר..."

**🎯 רמות עדיפות:**
🔥 דחוף - "זה דחוף"
⚡ חשוב - "זה חשוב"  
📋 רגיל - ברירת מחדל

פשוט שלח לי את המשימה ואני אטפל בכל השאר! 😊
        """
        
        keyboard = [[InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")]]
        
        await update.message.reply_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def button_handler(self, update: Update, context):
        """Handle inline keyboard callbacks with task management"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "ai_chat":
            await query.edit_message_text(
                "💬 **מצב שיחה פעיל!**\n\n"
                "שלח לי כל שאלה או נושא לדיון. אני כאן לעזור! 🤖\n\n"
                "**💡 דוגמאות למה שאני יכולה לעזור:**\n"
                "• תזכורות ומשימות: \"תזכור לי לקרוא לרופא מחר\"\n"
                "• פגישות: \"תקבע פגישה עם הצוות\"\n"
                "• מחקר: \"תחפש לי מידע על...\"\n"
                "• כתיבה: \"תעזור לי לכתוב אימייל\"\n"
                "• שאלות כלליות ועצות מקצועיות\n\n"
                "פשוט כתוב לי בעברית טבעית! 😊"
            )
            return AI_CHAT
            
        elif data == "my_tasks":
            # Show user tasks
            user_id = query.from_user.id
            all_tasks = getattr(self.db, 'tasks', {})
            user_tasks = [task for task in all_tasks.values() if task.get('user_id') == user_id]
            
            if not user_tasks:
                keyboard = [[
                    InlineKeyboardButton("➕ צור משימה ראשונה", callback_data="new_task"),
                    InlineKeyboardButton("❓ איך זה עובד?", callback_data="tasks_help")
                ]]
                
                await query.edit_message_text(
                    "📋 **המשימות שלי**\n\n"
                    "אין לך משימות פעילות כרגע.\n\n"
                    "💡 **איך יוצרים משימות?**\n"
                    "פשוט שלח לי הודעה כמו:\n"
                    "• \"תזכור לי לקרוא לרופא מחר\"\n"
                    "• \"תקבע פגישה עם הצוות השבוע\"\n"
                    "• \"תזכיר לי לשלוח דוח עד יום חמישי\"\n\n"
                    "אני אזהה אוטומטית שזו משימה ואיצור אותה עבורך! 🤖✨",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            # Display tasks
            pending_tasks = [t for t in user_tasks if t.get('status') == 'pending']
            completed_tasks = [t for t in user_tasks if t.get('status') == 'completed']
            
            tasks_text = f"📋 **המשימות שלי** ({len(pending_tasks)} פעילות)\n\n"
            
            priority_emoji = {'urgent': '🔥', 'high': '⚡', 'medium': '📋', 'low': '📝'}
            category_emoji = {
                'reminder': '⏰', 'meeting': '🤝', 'schedule': '📅', 
                'email': '📧', 'research': '🔍', 'call': '📞', 'document': '📄'
            }
            
            if pending_tasks:
                tasks_text += "**🟡 פעילות:**\n"
                for i, task in enumerate(pending_tasks[:5], 1):
                    emoji = category_emoji.get(task.get('category', 'other'), '📋')
                    priority = priority_emoji.get(task.get('priority', 'medium'), '📋')
                    
                    tasks_text += f"{i}. {emoji} {task['title'][:35]}...\n"
                    tasks_text += f"   {priority} {task.get('priority', 'medium')}"
                    
                    if task.get('due_date'):
                        try:
                            due_date = datetime.fromisoformat(task['due_date'])
                            tasks_text += f" | 📅 {due_date.strftime('%d/%m')}"
                        except:
                            pass
                    
                    tasks_text += "\n\n"
            
            if completed_tasks:
                tasks_text += f"**✅ הושלמו:** {len(completed_tasks)}\n\n"
            
            tasks_text += "💬 שלח לי משימה חדשה והיא תתווסף אוטומטית!"
            
            keyboard = [
                [InlineKeyboardButton("➕ משימה חדשה", callback_data="new_task")],
                [InlineKeyboardButton("✅ סמן הושלם", callback_data="complete_task")],
                [InlineKeyboardButton("⬅️ תפריט ראשי", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                tasks_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "new_task":
            await query.edit_message_text(
                "➕ **יצירת משימה חדשה**\n\n"
                "**🗣️ הדרך הקלה ביותר:**\n"
                "פשוט שלח לי הודעה בעברית טבעית!\n\n"
                "**📝 דוגמאות:**\n"
                "⏰ \"תזכור לי לקרוא לרופא מחר בשעה 10\"\n"
                "🤝 \"תקבע פגישה עם הצוות השבוע הבא\"\n"
                "📧 \"תזכיר לי לשלוח דוח עד יום חמישי\"\n"
                "🔍 \"תבדוק מחירים לנסיעה לברלין\"\n\n"
                "**🎯 רמות עדיפות:**\n"
                "🔥 דחוף - \"זה דחוף\"\n"
                "⚡ חשוב - \"זה חשוב\"\n"
                "📋 רגיל - ברירת מחדל\n\n"
                "אני אזהה את הסוג, העדיפות והתאריך אוטומטית! 🤖✨",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")
                ]])
            )
        
        elif data == "complete_task":
            # Show tasks to mark as complete
            user_id = query.from_user.id
            all_tasks = getattr(self.db, 'tasks', {})
            user_tasks = [task for task in all_tasks.values() 
                         if task.get('user_id') == user_id and task.get('status') == 'pending']
            
            if not user_tasks:
                await query.edit_message_text(
                    "✅ **סימון משימות כהושלמו**\n\n"
                    "אין לך משימות פעילות לסימון כרגע.\n"
                    "כל הכבוד! נראה שסיימת הכל! 🎉",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")
                    ]])
                )
                return
            
            # Create keyboard with tasks to complete
            keyboard = []
            for task in user_tasks[:8]:  # Show max 8 tasks
                keyboard.append([InlineKeyboardButton(
                    f"✅ {task['title'][:30]}...",
                    callback_data=f"complete_{task['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("⬅️ חזור", callback_data="my_tasks")])
            
            await query.edit_message_text(
                "✅ **בחר משימה לסימון כהושלמה:**\n\n"
                "לחץ על המשימה שסיימת:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data.startswith("complete_"):
            # Mark specific task as complete
            task_id = data.replace("complete_", "")
            
            if hasattr(self.db, 'tasks') and task_id in self.db.tasks:
                task = self.db.tasks[task_id]
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                
                await query.edit_message_text(
                    f"🎉 **משימה הושלמה!**\n\n"
                    f"✅ {task['title']}\n\n"
                    f"כל הכבוד! המשימה סומנה כהושלמה.\n"
                    f"⏰ הושלמה: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📋 למשימות שלי", callback_data="my_tasks"),
                        InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")
                    ]])
                )
            else:
                await query.edit_message_text(
                    "❌ לא מצאתי את המשימה. יכול להיות שהיא כבר נמחקה.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")
                    ]])
                )
        
        elif data == "tasks_help":
            await query.edit_message_text(
                "❓ **איך מערכת המשימות עובדת?**\n\n"
                "**🤖 זיהוי אוטומטי:**\n"
                "אני מזהה אוטומטית כשאתה שולח לי משימה בשיחה רגילה!\n\n"
                "**🎯 מילות מפתח שאני מזהה:**\n"
                "⏰ תזכורות: \"תזכור\", \"תזכיר\", \"אל תשכח\"\n"
                "🤝 פגישות: \"פגישה\", \"ישיבה\", \"מפגש\"\n"
                "📅 תזמון: \"תזמן\", \"קבע\", \"לוח זמנים\"\n"
                "📧 אימיילים: \"אימייל\", \"מייל\", \"שלח הודעה\"\n"
                "🔍 מחקר: \"חפש\", \"מצא\", \"בדוק\"\n\n"
                "**📅 זיהוי תאריכים:**\n"
                "• \"היום\" - היום\n"
                "• \"מחר\" - מחר\n" 
                "• \"השבוע\" - השבוע הזה\n"
                "• \"השבוע הבא\" - השבוע הבא\n\n"
                "**🎯 רמות עדיפות:**\n"
                "🔥 דחוף - \"דחוף\", \"מיידי\", \"חירום\"\n"
                "⚡ חשוב - \"חשוב\", \"priority\"\n"
                "📋 רגיל - ברירת מחדל\n\n"
                "פשוט תדבר איתי כרגיל ואני אטפל בשאר! 😊",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")
                ]])
            )
            
        elif data == "settings":
            keyboard = [
                [InlineKeyboardButton("🌐 שפה", callback_data="lang_settings")],
                [InlineKeyboardButton("🔔 התראות", callback_data="notif_settings")],
                [InlineKeyboardButton("📋 ניהול משימות", callback_data="task_settings")],
                [InlineKeyboardButton("🗑️ מחק היסטוריה", callback_data="clear_history")],
                [InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⚙️ **הגדרות מאיה**\n\nבחר את האפשרות שתרצה לערוך:",
                reply_markup=reply_markup
            )
            return SETTINGS_MENU
        
        elif data == "task_settings":
            await query.edit_message_text(
                "📋 **הגדרות ניהול משימות**\n\n"
                "**🤖 זיהוי אוטומטי:** פעיל\n"
                "כשאתה שולח הודעה עם מילות מפתח למשימות, אני יוצרת אותן אוטומטית.\n\n"
                "**📅 תזכורות:** זמין בקרוב\n"
                "בעתיד אוכל לשלוח לך תזכורות על משימות שמתקרבות.\n\n"
                "**📊 סטטיסטיקות:**\n"
                "• משימות שיצרת: מעקב אוטומטי\n"
                "• משימות שהושלמו: מעקב אוטומטי\n"
                "• ממוצע זמן השלמה: בפיתוח\n\n"
                "💡 הצעות לשיפור? שתף איתי בשיחה!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ חזור להגדרות", callback_data="settings")
                ]])
            )
            
        elif data == "stats":
            # Enhanced stats with task information
            stats = self.db.get_basic_stats()
            
            # Add task stats
            user_id = query.from_user.id
            all_tasks = getattr(self.db, 'tasks', {})
            user_tasks = [task for task in all_tasks.values() if task.get('user_id') == user_id]
            
            pending_tasks = len([t for t in user_tasks if t.get('status') == 'pending'])
            completed_tasks = len([t for t in user_tasks if t.get('status') == 'completed'])
            
            stats_text = f"""
📊 **סטטיסטיקות הבוט:**

👥 **משתמשים רשומים:** {stats.get('total_users', 0)}
⚡ **פעילים השבוע:** {stats.get('active_users_week', 0)}
💬 **סה"כ שיחות:** {stats.get('total_conversations', 0)}

📋 **המשימות שלך:**
🟡 **פעילות:** {pending_tasks}
✅ **הושלמו:** {completed_tasks}
📈 **סה"כ יצרת:** {len(user_tasks)}

🤖 **מצב המערכת:**
🟢 **AI Engine:** פעיל
🟢 **Task Manager:** פעיל
🟢 **Status:** {stats.get('uptime', 'Online')}

אני לומדת ומשתפרת מכל שיחה ומשימה! 💜
            """
            
            keyboard = [[InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(stats_text, reply_markup=reply_markup)
            
        elif data == "help":
            help_text = """
❓ **מדריך שימוש במאיה**

🎯 **מה אני יכולה לעשות:**
• לענות על שאלות בכל נושא
• ליצור ולנהל משימות חכמות
• לעזור בכתיבה ועריכה
• לתת הסברים על נושאים מורכבים
• לסייע במשימות מזכירות יומיומיות
• ללמוד מההעדפות שלך

📋 **ניהול משימות חכם:**
• שלח "תזכור לי..." - ואני אשמור תזכורת
• שלח "תקבע פגישה..." - ואני אארגן פגישה
• שלח "תבדוק..." - ואני אכין משימת מחקר
• אני מזהה אוטומטית תאריכים ועדיפויות

💡 **טיפים לשימוש:**
• כתוב בעברית טבעית - אני מבינה!
• תאר בפירוט מה אתה צריך
• השתמש במילים כמו "דחוף" לעדיפות גבוהה
• אל תהסס לשאול שאלות המשך

🔧 **פקודות זמינות:**
/start - התחלה מחדש
/tasks - המשימות שלי
/stats - סטטיסטיקות אישיות
/feedback - שליחת משוב

🤖 אני כאן 24/7 לעזור לך להיות יותר מאורגן ויעיל!
            """
            
            keyboard = [[InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(help_text, reply_markup=reply_markup)
            
        elif data == "main_menu":
            # Enhanced main menu with task info
            user_id = query.from_user.id
            all_tasks = getattr(self.db, 'tasks', {})
            user_tasks = [task for task in all_tasks.values() if task.get('user_id') == user_id]
            pending_tasks = len([t for t in user_tasks if t.get('status') == 'pending'])
            
            keyboard = [
                [InlineKeyboardButton("💬 שיחה עם AI", callback_data="ai_chat")],
                [InlineKeyboardButton(
                    f"📋 המשימות שלי ({pending_tasks})", 
                    callback_data="my_tasks"
                )],
                [InlineKeyboardButton("⚙️ הגדרות", callback_data="settings")],
                [InlineKeyboardButton("📊 סטטיסטיקות", callback_data="stats")],
                [InlineKeyboardButton("❓ עזרה", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_text = "🤖 **מאיה - המזכירה החכמה שלך**\n\n"
            if pending_tasks > 0:
                welcome_text += f"📋 יש לך {pending_tasks} משימות פעילות\n\n"
            welcome_text += "מה תרצה לעשות?"
            
            await query.edit_message_text(
                welcome_text,
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
    application.add_handler(CommandHandler("tasks", maya.tasks_command))  # New task command
    application.add_handler(CommandHandler("newtask", maya.new_task_command))  # New task help
    
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
