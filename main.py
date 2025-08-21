#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maya - Advanced AI Telegram Bot
=====================================
A sophisticated AI-powered Telegram bot with autonomous capabilities,
Hebrew support, and advanced conversation management.

Author: AI Development Team
Version: 2.1 (Fixed & Enhanced)
License: MIT
"""

import os
import logging
import asyncio
import json
from datetime import datetime, timedelta
from threading import Thread
from typing import Dict, List, Optional, Any, Tuple
import re
from functools import wraps
import uuid

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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

# Intelligent Maya Agent
from intelligent_maya import IntelligentMayaAgent, init_intelligent_maya, intelligent_maya, smart_response

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

# Conversation states for complex interactions
MAIN_MENU, SETTINGS_MENU, AI_CHAT, FEEDBACK = range(4)

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
        "version": "2.1"
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
    stop_words = {'של', 'את', 'על', 'אל', 'כל', 'מה', 'זה', 'זו', 'היא', 'הוא'}
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    return keywords[:10]  # Return top 10 keywords

def validate_user_input(text: str) -> bool:
    """Validate user input for security"""
    if not text or len(text) > 4000:
        return False
    # Check for dangerous patterns
    dangerous_patterns = ['<script>', 'javascript:', 'data:', 'vbscript:', 'onload=']
    return not any(pattern in text.lower() for pattern in dangerous_patterns)

# ============================
# DATABASE MANAGEMENT
# ============================

class DatabaseManager:
    """Advanced database management with MongoDB and fallback"""

    def __init__(self):
        self.client = None
        self.db = None
        self.users = None
        self.conversations = None
        self.ai_memory = None
        self.tasks = {}  # Initialize tasks storage
        self.tasks_collection = None
        self._connect()

    def _connect(self):
        """Establish database connection with improved error handling"""
        try:
            if MONGO_URI:
                self.client = MongoClient(
                    MONGO_URI, 
                    serverSelectionTimeoutMS=5000,
                    maxPoolSize=50,
                    retryWrites=True
                )
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client.maya_bot
                self.users = self.db.users
                self.conversations = self.db.conversations
                self.ai_memory = self.db.ai_memory
                self.tasks_collection = self.db.tasks
                
                # Create indexes for better performance
                self._create_indexes()
                
                logger.info("✅ Connected to MongoDB successfully")
            else:
                logger.warning("⚠️ No MongoDB URI provided - using in-memory storage")
                self._setup_fallback_storage()
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self._setup_fallback_storage()
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            self._setup_fallback_storage()

    def _setup_fallback_storage(self):
        """Setup in-memory storage as fallback"""
        self.users = {}
        self.conversations = []
        self.ai_memory = {}

    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            if self.users:
                self.users.create_index("user_id", unique=True)
                self.users.create_index("last_seen")
            
            if self.conversations:
                self.conversations.create_index([("user_id", 1), ("timestamp", -1)])
            
            if self.tasks_collection:
                self.tasks_collection.create_index([("user_id", 1), ("status", 1)])
                self.tasks_collection.create_index("created_at")
                
            logger.info("✅ Database indexes created successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create indexes: {e}")

    def register_user(self, user_data: Dict) -> bool:
        """Register or update user information with enhanced validation"""
        try:
            # Validate input
            if not user_data.get('user_id'):
                return False

            user_id = user_data["user_id"]
            
            if hasattr(self.users, 'update_one'):  # MongoDB
                result = self.users.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            **user_data,
                            "last_seen": datetime.now(),
                            "is_active": True,
                            "updated_at": datetime.now()
                        },
                        "$setOnInsert": {
                            "first_join": datetime.now(),
                            "total_messages": 0,
                            "preferences": {"language": "he", "notifications": True},
                            "created_at": datetime.now()
                        },
                        "$inc": {"total_messages": 1}
                    },
                    upsert=True
                )
                return result.acknowledged
            else:  # In-memory storage
                if user_id not in self.users:
                    self.users[user_id] = {
                        **user_data,
                        "first_join": datetime.now(),
                        "total_messages": 1,
                        "preferences": {"language": "he", "notifications": True},
                        "created_at": datetime.now(),
                        "is_active": True
                    }
                else:
                    self.users[user_id].update(user_data)
                    self.users[user_id]["total_messages"] += 1
                    self.users[user_id]["last_seen"] = datetime.now()
                    self.users[user_id]["updated_at"] = datetime.now()
                return True
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False

    def log_conversation(self, user_id: int, message: str, response: str, 
                        message_type: str = "text", metadata: Dict = None) -> bool:
        """Enhanced conversation logging with metadata support"""
        try:
            conversation_data = {
                "user_id": user_id,
                "timestamp": datetime.now(),
                "user_message": message[:1000],  # Limit message length
                "bot_response": response[:2000],  # Limit response length
                "message_type": message_type,
                "response_length": len(response),
                "ai_model": "gemini-pro",
                "metadata": metadata or {}
            }

            if hasattr(self.conversations, 'insert_one'):  # MongoDB
                result = self.conversations.insert_one(conversation_data)
                return result.acknowledged
            else:  # In-memory storage
                self.conversations.append(conversation_data)
                # Keep only last 1000 conversations in memory
                if len(self.conversations) > 1000:
                    self.conversations = self.conversations[-1000:]
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
        """Get basic bot statistics with enhanced data"""
        try:
            if hasattr(self.users, 'count_documents'):  # MongoDB
                total_users = self.users.count_documents({})
                active_users = self.users.count_documents({
                    "last_seen": {"$gte": datetime.now() - timedelta(days=7)}
                })
                total_conversations = self.conversations.count_documents({})
                today_conversations = self.conversations.count_documents({
                    "timestamp": {"$gte": datetime.now().replace(hour=0, minute=0, second=0)}
                })
            else:  # In-memory storage
                total_users = len(self.users)
                week_ago = datetime.now() - timedelta(days=7)
                active_users = sum(
                    1 for user in self.users.values()
                    if user.get("last_seen", datetime.min) > week_ago
                )
                total_conversations = len(self.conversations)
                today = datetime.now().date()
                today_conversations = sum(
                    1 for conv in self.conversations
                    if conv.get("timestamp", datetime.min).date() == today
                )

            return {
                "total_users": total_users,
                "active_users_week": active_users,
                "total_conversations": total_conversations,
                "today_conversations": today_conversations,
                "uptime": "Online",
                "database_type": "MongoDB" if hasattr(self.users, 'count_documents') else "Memory"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

    def get_task_statistics(self, user_id: int = None) -> Dict:
        """Get comprehensive task statistics"""
        try:
            if not hasattr(self, 'tasks') and not self.tasks_collection:
                return {'error': 'No task system available'}

            if self.tasks_collection and hasattr(self.tasks_collection, 'find'):
                # MongoDB query
                query = {"user_id": user_id} if user_id else {}
                all_tasks = list(self.tasks_collection.find(query))
            else:
                # In-memory query
                all_tasks = list(self.tasks.values())
                if user_id:
                    all_tasks = [task for task in all_tasks if task.get('user_id') == user_id]

            if not all_tasks:
                return {
                    'total': 0, 'by_status': {}, 'by_category': {}, 
                    'by_priority': {}, 'created_today': 0, 'completed_today': 0
                }

            # Count by status
            by_status = {}
            for task in all_tasks:
                status = task.get('status', 'pending')
                by_status[status] = by_status.get(status, 0) + 1

            # Count by category
            by_category = {}
            for task in all_tasks:
                category = task.get('category', 'other')
                by_category[category] = by_category.get(category, 0) + 1

            # Count by priority
            by_priority = {}
            for task in all_tasks:
                priority = task.get('priority', 'medium')
                by_priority[priority] = by_priority.get(priority, 0) + 1

            return {
                'total': len(all_tasks),
                'by_status': by_status,
                'by_category': by_category,
                'by_priority': by_priority,
                'created_today': len([t for t in all_tasks if self._is_today(t.get('created_at', ''))]),
                'completed_today': len([t for t in all_tasks if self._is_today(t.get('completed_at', ''))])
            }

        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {'error': str(e)}

    def _is_today(self, date_string: str) -> bool:
        """Check if a date string is from today"""
        if not date_string:
            return False
        try:
            if isinstance(date_string, datetime):
                date = date_string
            else:
                date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            today = datetime.now().date()
            return date.date() == today
        except:
            return False

    def save_task(self, task_data: Dict) -> bool:
        """Save task to database"""
        try:
            if self.tasks_collection and hasattr(self.tasks_collection, 'insert_one'):
                result = self.tasks_collection.insert_one(task_data)
                return result.acknowledged
            else:
                self.tasks[task_data['id']] = task_data
                return True
        except Exception as e:
            logger.error(f"Error saving task: {e}")
            return False

    def update_task(self, task_id: str, updates: Dict) -> bool:
        """Update existing task"""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            if self.tasks_collection and hasattr(self.tasks_collection, 'update_one'):
                result = self.tasks_collection.update_one(
                    {"id": task_id},
                    {"$set": updates}
                )
                return result.modified_count > 0
            else:
                if task_id in self.tasks:
                    self.tasks[task_id].update(updates)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False

    def get_user_tasks(self, user_id: int, status: str = None) -> List[Dict]:
        """Get user tasks with optional status filter"""
        try:
            if self.tasks_collection and hasattr(self.tasks_collection, 'find'):
                query = {"user_id": user_id}
                if status:
                    query["status"] = status
                return list(self.tasks_collection.find(query).sort("created_at", -1))
            else:
                tasks = [task for task in self.tasks.values() if task.get('user_id') == user_id]
                if status:
                    tasks = [task for task in tasks if task.get('status') == status]
                return sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as e:
            logger.error(f"Error getting user tasks: {e}")
            return []

    def __del__(self):
        """Cleanup database connections"""
        try:
            if self.client:
                self.client.close()
        except:
            pass
# ============================
# TASK MANAGEMENT SYSTEM
# ============================

class TaskManager:
    """Smart task management with AI integration"""

    def __init__(self, db):
        self.db = db

    def analyze_user_intent(self, message: str) -> Optional[Tuple[str, int]]:
        """Analyze user intent with confidence scoring"""
        task_patterns = {
            'reminder': ['תזכור', 'תזכיר', 'אל תשכח', 'reminder', 'תזכורת', 'תזכרי'],
            'meeting': ['פגישה', 'ישיבה', 'מפגש', 'meeting', 'פגש', 'נפגש'],
            'schedule': ['תזמן', 'קבע', 'לוח זמנים', 'schedule', 'ארגן', 'תכנן'],
            'email': ['אימייל', 'מייל', 'שלח הודעה', 'email', 'כתוב', 'הודעה'],
            'research': ['חפש', 'מצא', 'מחקר', 'research', 'בדוק', 'תחקור'],
            'call': ['תתקשר', 'שיחה', 'טלפון', 'call', 'חייג', 'התקשר'],
            'document': ['מסמך', 'דוח', 'כתוב', 'document', 'הכן', 'תכין'],
            'purchase': ['קנה', 'רכוש', 'הזמן', 'buy', 'purchase', 'שילם'],
            'travel': ['נסיעה', 'נסע', 'טיסה', 'travel', 'חופשה', 'יציאה']
        }

        confidence_scores = {}
        message_lower = message.lower()

        for intent, keywords in task_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                confidence_scores[intent] = score

        return max(confidence_scores.items(), key=lambda x: x[1]) if confidence_scores else None

    def extract_task_details(self, message: str) -> Dict:
        """Extract task details from message with enhanced parsing"""
        intent_result = self.analyze_user_intent(message)
        intent = intent_result[0] if intent_result else 'other'

        # Extract priority with more keywords
        priority_keywords = {
            'urgent': ['דחוף', 'מיידי', 'חירום', 'urgent', 'עכשיו', 'הכי חשוב'],
            'high': ['חשוב', 'priority', 'גבוה', 'מהר', 'בהקדם'],
            'low': ['לא דחוף', 'כשיהיה זמן', 'low', 'בזמן פנוי', 'אין עניין']
        }

        priority = 'medium'  # default
        message_lower = message.lower()

        for level, keywords in priority_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                priority = level
                break

        # Extract due date with improved parsing
        due_date = self._extract_due_date(message)

        # Generate title - clean and concise
        title = self._clean_title(message)

        return {
            'title': title,
            'description': message,
            'category': intent,
            'priority': priority,
            'due_date': due_date,
            'status': 'pending'
        }

    def _clean_title(self, message: str) -> str:
        """Clean and create a proper title from message"""
        # Remove common prefixes
        prefixes_to_remove = ['תזכור לי', 'תזכיר לי', 'אל תשכח', 'תקבע', 'תחפש', 'תבדוק']
        title = message
        
        for prefix in prefixes_to_remove:
            if title.lower().startswith(prefix.lower()):
                title = title[len(prefix):].strip()
        
        # Remove common words that start sentences
        if title.lower().startswith('ש'):
            title = title[1:].strip()
        if title.lower().startswith('ל'):
            title = title[1:].strip()
            
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        # Limit length
        return title[:60] + "..." if len(title) > 60 else title

    def _extract_due_date(self, message: str) -> Optional[str]:
        """Extract due date from natural language with improved parsing"""
        message_lower = message.lower()
        today = datetime.now()

        # Immediate/today
        if any(word in message_lower for word in ['היום', 'today', 'עכשיו', 'מיידי']):
            return today.isoformat()
        
        # Tomorrow
        elif any(word in message_lower for word in ['מחר', 'tomorrow']):
            return (today + timedelta(days=1)).isoformat()
        
        # Day after tomorrow
        elif any(word in message_lower for word in ['מחרתיים', 'day after tomorrow']):
            return (today + timedelta(days=2)).isoformat()
        
        # This week
        elif any(word in message_lower for word in ['השבוע', 'this week', 'השבוע הזה']):
            return (today + timedelta(days=7)).isoformat()
        
        # Next week
        elif any(word in message_lower for word in ['השבוע הבא', 'next week']):
            return (today + timedelta(days=14)).isoformat()
        
        # This month
        elif any(word in message_lower for word in ['החודש', 'this month', 'החודש הזה']):
            return (today + timedelta(days=30)).isoformat()
        
        # Next month
        elif any(word in message_lower for word in ['החודש הבא', 'next month']):
            return (today + timedelta(days=60)).isoformat()

        # Try to find specific day names
        days_hebrew = {
            'ראשון': 0, 'שני': 1, 'שלישי': 2, 'רביעי': 3, 'חמישי': 4, 'שישי': 5, 'שבת': 6,
            'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4, 'friday': 5, 'saturday': 6
        }
        
        for day_name, day_num in days_hebrew.items():
            if day_name in message_lower:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).isoformat()

        return None

    def _save_task(self, task_details: Dict) -> str:
        """Save task to storage with improved structure"""
        task_id = str(uuid.uuid4())[:8]  # Shorter ID for easier use
        task_details['id'] = task_id
        task_details['created_at'] = datetime.now().isoformat()
        task_details['updated_at'] = datetime.now().isoformat()

        # Ensure all tasks have required fields
        task_details.setdefault('status', 'pending')
        task_details.setdefault('priority', 'medium')
        task_details.setdefault('category', 'other')

        # Save to database
        success = self.db.save_task(task_details)
        
        if success:
            logger.info(f"Task created: {task_id} - {task_details['title']}")
            return task_id
        else:
            logger.error(f"Failed to save task: {task_id}")
            return None

    def get_task_category_display(self, category: str) -> Dict:
        """Get formatted category with emoji and metadata"""
        category_map = {
            'reminder': {'emoji': '⏰', 'name': 'תזכורת', 'color': 'blue'},
            'meeting': {'emoji': '🤝', 'name': 'פגישה', 'color': 'green'},
            'schedule': {'emoji': '📅', 'name': 'לוח זמנים', 'color': 'purple'},
            'email': {'emoji': '📧', 'name': 'אימייל', 'color': 'red'},
            'research': {'emoji': '🔍', 'name': 'מחקר', 'color': 'orange'},
            'call': {'emoji': '📞', 'name': 'שיחה', 'color': 'cyan'},
            'document': {'emoji': '📄', 'name': 'מסמך', 'color': 'gray'},
            'purchase': {'emoji': '🛒', 'name': 'רכישה', 'color': 'yellow'},
            'travel': {'emoji': '✈️', 'name': 'נסיעה', 'color': 'teal'}
        }
        return category_map.get(category, {'emoji': '📋', 'name': 'משימה', 'color': 'gray'})

    def get_priority_display(self, priority: str) -> Dict:
        """Get formatted priority with emoji and metadata"""
        priority_map = {
            'urgent': {'emoji': '🔥', 'name': 'דחוף', 'color': 'red'},
            'high': {'emoji': '⚡', 'name': 'חשוב', 'color': 'orange'},
            'medium': {'emoji': '📋', 'name': 'רגיל', 'color': 'blue'},
            'low': {'emoji': '📝', 'name': 'נמוך', 'color': 'gray'}
        }
        return priority_map.get(priority, {'emoji': '📋', 'name': 'רגיל', 'color': 'blue'})

    async def create_and_notify_task(self, user_id: int, message: str) -> Optional[Tuple[str, InlineKeyboardMarkup, str]]:
        """Create task and return with interactive keyboard"""
        intent_result = self.analyze_user_intent(message)

        if not intent_result:
            return None

        intent, confidence = intent_result

        # Only create task if confidence is high enough and intent is task-related
        if confidence >= 1 and intent in ['reminder', 'meeting', 'schedule', 'email', 'research', 'call', 'document', 'purchase', 'travel']:
            task_details = self.extract_task_details(message)
            task_details['user_id'] = user_id
            task_details['created_by_ai'] = True

            # Save task
            task_id = self._save_task(task_details)
            
            if not task_id:
                return None

            # Get display info
            category_info = self.get_task_category_display(task_details['category'])
            priority_info = self.get_priority_display(task_details['priority'])

            # Create response message
            response = f"""✅ יצרתי עבורך משימה חדשה!

{category_info['emoji']} **{task_details['title']}**
{priority_info['emoji']} עדיפות: {priority_info['name']}"""

            if task_details.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(task_details['due_date'])
                    response += f"\n📅 תאריך יעד: {due_date.strftime('%d/%m/%Y')}"
                except:
                    pass

            # Create interactive keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ סמן כהושלם", callback_data=f"complete_{task_id}"),
                    InlineKeyboardButton("✏️ ערוך", callback_data=f"edit_{task_id}")
                ],
                [
                    InlineKeyboardButton("📋 כל המשימות", callback_data="my_tasks"),
                    InlineKeyboardButton("🔄 המשך שיחה", callback_data="continue_chat")
                ]
            ]

            return response, InlineKeyboardMarkup(keyboard), task_id

        return None

    def get_user_tasks_summary(self, user_id: int) -> Dict:
        """Get comprehensive user tasks summary"""
        try:
            user_tasks = self.db.get_user_tasks(user_id)

            summary = {
                'total': len(user_tasks),
                'pending': len([t for t in user_tasks if t.get('status') == 'pending']),
                'completed': len([t for t in user_tasks if t.get('status') == 'completed']),
                'in_progress': len([t for t in user_tasks if t.get('status') == 'in_progress']),
                'urgent': len([t for t in user_tasks if t.get('priority') == 'urgent' and t.get('status') == 'pending']),
                'overdue': 0  # Will be calculated with due dates
            }

            # Calculate overdue tasks
            now = datetime.now()
            for task in user_tasks:
                if task.get('status') == 'pending' and task.get('due_date'):
                    try:
                        due_date = datetime.fromisoformat(task['due_date'])
                        if due_date < now:
                            summary['overdue'] += 1
                    except:
                        pass

            return summary
        except Exception as e:
            logger.error(f"Error getting tasks summary: {e}")
            return {'total': 0, 'pending': 0, 'completed': 0, 'in_progress': 0, 'urgent': 0, 'overdue': 0}

    def complete_task(self, task_id: str, user_id: int) -> bool:
        """Mark task as completed"""
        try:
            updates = {
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            }
            return self.db.update_task(task_id, updates)
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}")
            return False

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
        """Initialize Gemini AI model with enhanced configuration"""
        try:
            if GEMINI_API_KEY:
                # Configure model settings for better Hebrew support
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
                              user_name: str = "משתמש") -> Tuple[str, Optional[InlineKeyboardMarkup], Optional[str]]:
        """Generate intelligent response with enhanced task management"""
        try:
            # Validate input
            if not validate_user_input(message):
                return "מצטערת, ההודעה מכילה תוכן לא תקין. אנא נסה שוב.", None, None

            if not self.model:
                return self._fallback_response(message), None, None

            # Analyze user intent first
            intent = self.task_manager.analyze_user_intent(message)

            # Get user task summary for context
            task_summary = self.task_manager.get_user_tasks_summary(user_id)

            # Build rich context with task awareness
            context = await self._build_rich_context(user_id, message, intent, task_summary, user_name)

            # Generate AI response
            ai_response = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync, context
            )

            # Try to create task if relevant
            task_result = await self.task_manager.create_and_notify_task(user_id, message)

            if task_result:
                task_message, task_keyboard, task_id = task_result

                # Combine AI response with task creation
                combined_response = f"""{ai_response}

---

{task_message}"""

                # Log conversation with task reference
                self.db.log_conversation(
                    user_id, message, combined_response, 
                    metadata={"task_created": task_id, "intent": intent[0] if intent else None}
                )

                return combined_response, task_keyboard, task_id
            else:
                # No task created, return regular response with smart keyboard
                smart_keyboard = self._create_context_keyboard(message, user_id, intent)

                # Log regular conversation
                self.db.log_conversation(
                    user_id, message, ai_response,
                    metadata={"intent": intent[0] if intent else None}
                )

                return ai_response, smart_keyboard, None

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            fallback = self._fallback_response(message)
            return fallback, None, None

    async def _build_rich_context(self, user_id: int, message: str, intent=None, 
                                task_summary=None, user_name: str = "משתמש") -> str:
        """Build comprehensive context with task and user awareness"""
        # Get conversation history
        context = self.db.get_user_context(user_id, last_n=3)

        # Get recent tasks
        user_tasks = self.db.get_user_tasks(user_id)[:5]

        # Build context string
        context_str = ""
        if context:
            context_str = "\n\nהיסטוריית השיחה האחרונה:\n"
            for i, conv in enumerate(reversed(context), 1):
                context_str += f"{i}. משתמש: {conv['user_message'][:100]}...\n"
                context_str += f"   מאיה: {conv['bot_response'][:100]}...\n"

        # Add task context
        tasks_str = ""
        if user_tasks:
            pending_tasks = [t for t in user_tasks if t.get('status') == 'pending']
            completed_tasks = [t for t in user_tasks if t.get('status') == 'completed']

            if pending_tasks:
                tasks_str = f"\n\nמשימות פעילות של המשתמש ({len(pending_tasks)}):\n"
                for task in pending_tasks[:3]:
                    category_info = self.task_manager.get_task_category_display(task.get('category', 'other'))
                    priority_info = self.task_manager.get_priority_display(task.get('priority', 'medium'))
                    tasks_str += f"• {category_info['emoji']} {task['title']} ({priority_info['name']})\n"

            if completed_tasks:
                tasks_str += f"\nמשימות שהושלמו לאחרונה: {len(completed_tasks)}\n"

        # Add task summary
        summary_str = ""
        if task_summary and task_summary['total'] > 0:
            summary_str = f"\n\nסיכום משימות של {user_name}:"
            summary_str += f"\n• סה״כ משימות: {task_summary['total']}"
            summary_str += f"\n• פעילות: {task_summary['pending']}"
            summary_str += f"\n• הושלמו: {task_summary['completed']}"
            if task_summary['urgent'] > 0:
                summary_str += f"\n• דחופות: {task_summary['urgent']}"
            if task_summary['overdue'] > 0:
                summary_str += f"\n• איחור: {task_summary['overdue']}"

        # Intent context
        intent_str = ""
        if intent:
            intent_str = f"\n\nכוונה מזוהה: {intent[0]} (ביטחון: {intent[1]})"
            if intent[0] in ['reminder', 'meeting', 'schedule', 'email', 'research']:
                intent_str += "\n(הכן ליצור משימה אוטומטית)"

        return f"""
{MAYA_PERSONALITY}

כמזכירה אישית חכמה ואקטיבית, תפקידי הוא:
- להבין כוונות ולזהות משימות אוטומטות
- לנהל משימות ותזכורות בצורה פרואקטיבית
- לספק מעקב ועדכונים על התקדמות
- להיות זמינה ומגיבה לצרכים משתנים
- לתת עצות חכמות ומותאמות אישית

{context_str}{tasks_str}{summary_str}{intent_str}

ההודעה הנוכחית מ{user_name}: "{message}"

הגב בעברית טבעית וידידותית. 
אם זיהיתי כוונה למשימה - הסבר מה אני עושה.
התייחס למשימות קיימות ולהיסטוריה אם רלוונטי.
תן עצות פרואקטיביות לניהול זמן וארגון.
השתמש בשם המשתמש באופן טבעי בתשובה.
"""

    def _create_context_keyboard(self, message: str, user_id: int, intent=None) -> InlineKeyboardMarkup:
        """Create smart context-aware keyboard"""
        keyboard = []

        # Task-related buttons if intent detected
        if intent and intent[0] in ['reminder', 'meeting', 'schedule', 'email', 'research', 'call', 'document']:
            keyboard.append([
                InlineKeyboardButton("📋 המשימות שלי", callback_data="my_tasks"),
                InlineKeyboardButton("➕ משימה חדשה", callback_data="new_task")
            ])

        # Get task summary for smart suggestions
        task_summary = self.task_manager.get_user_tasks_summary(user_id)

        if task_summary['urgent'] > 0:
            keyboard.append([
                InlineKeyboardButton(f"🔥 משימות דחופות ({task_summary['urgent']})", callback_data="urgent_tasks")
            ])

        if task_summary['overdue'] > 0:
            keyboard.append([
                InlineKeyboardButton(f"⏰ משימות באיחור ({task_summary['overdue']})", callback_data="overdue_tasks")
            ])

        # Always available options
        keyboard.extend([
            [InlineKeyboardButton("🔄 המשך שיחה", callback_data="continue_chat")],
            [InlineKeyboardButton("📊 סיכום משימות", callback_data="task_summary")],
            [InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")]
        ])

        return InlineKeyboardMarkup(keyboard)

    def _generate_sync(self, prompt: str) -> str:
        """Synchronous generation wrapper with error handling"""
        try:
            response = self.model.generate_content(prompt)
            if response.text:
                return response.text
            else:
                return "מצטערת, לא הצלחתי לחשוב על תשובה כרגע. תוכל לנסח את השאלה אחרת?"
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise e

    def _fallback_response(self, message: str) -> str:
        """Enhanced fallback responses with task awareness"""
        message_lower = message.lower()

        # Task-related fallbacks
        if any(word in message_lower for word in ["תזכור", "פגישה", "משימה", "תקבע", "תחפש"]):
            return ("אני מזכירה אישית חכמה! כרגע יש לי בעיה טכנית קטנה עם מערכת ה-AI, "
                   "אבל בקרוב אוכל לעזור לך עם משימות ותזכורות! 🗓️\n\n"
                   "בינתיים, תוכל להשתמש בתפריט כדי לנהל משימות ידנית.")

        # Regular fallbacks
        if any(word in message_lower for word in ["שלום", "היי", "מה נשמע", "בוקר טוב"]):
            return ("שלום! אני מאיה, המזכירה האישית החכמה שלך! 😊\n\n"
                   "אני יכולה לעזור עם:\n"
                   "• תזכורות ומשימות\n"
                   "• פגישות ולוח זמנים\n"
                   "• מחקר ומידע\n"
                   "• כתיבה ועריכה\n\n"
                   "איך אוכל לעזור לך היום?")
        elif any(word in message_lower for word in ["תודה", "תנקיו", "אין בעד מה"]):
            return "אין בעד מה! זה התפקיד שלי לעזור לך! 💜\nאם יש עוד משהו - אני כאן!"
        elif "?" in message:
            return ("זו שאלה מעניינת! כרגע אני חוות קשיים טכניים קטנים, "
                   "אבל חזור אליי בעוד רגע ואתן לך תשובה מפורטת 🤔\n\n"
                   "בינתיים, אולי אוכל לעזור לך דרך התפריט?")

        return ("מצטערת, אני חווה קשיים טכניים כרגע. אבל אני עדיין יכולה לעזור לך! 🤖\n\n"
               "נסה להשתמש בתפריט או פשוט כתוב לי שוב - לפעמים זה עוזר! ✨")

# ============================
# BOT HANDLERS
# ============================

class MayaBot:
    """Main bot class with all handlers"""

    def __init__(self):
        # Initialize database first
        self.db = DatabaseManager()
        
        # Initialize intelligent Maya agent if Gemini API key is available
        if GEMINI_API_KEY:
            self.intelligent_agent = init_intelligent_maya(GEMINI_API_KEY)
            logger.info("✅ IntelligentMayaAgent initialized successfully")
        else:
            self.intelligent_agent = None
            logger.warning("⚠️ No Gemini API key - IntelligentMayaAgent disabled")
            
        # Keep the traditional AI as backup
        self.ai = MayaAI()
        
        # Use the same DB instance
        self.ai.db = self.db

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

        # Get task summary for personalized welcome
        task_summary = self.ai.task_manager.get_user_tasks_summary(user.id)

        # Create main menu keyboard with task info
        keyboard = [
            [InlineKeyboardButton("💬 שיחה עם AI", callback_data="ai_chat")],
            [InlineKeyboardButton(
                f"📋 המשימות שלי ({task_summary['pending']})", 
                callback_data="my_tasks"
            )],
            [InlineKeyboardButton("⚙️ הגדרות", callback_data="settings")],
            [InlineKeyboardButton("📊 סטטיסטיקות", callback_data="stats")],
            [InlineKeyboardButton("❓ עזרה", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = f"""
🤖 שלום {user.first_name}, אני מאיה!

אני בוט AI מתקדם שיכול לעזור לך במגוון נושאים:
• שיחות טבעיות בעברית
• יצירת וניהול משימות חכמות
• תזכורות ותזמון פגישות
• עזרה במשימות יומיומיות
• למידה מכל שיחה שלנו"""

        if task_summary['pending'] > 0:
            welcome_text += f"\n\n📋 יש לך {task_summary['pending']} משימות פעילות"
            if task_summary['urgent'] > 0:
                welcome_text += f" (כולל {task_summary['urgent']} דחופות! 🔥)"

        welcome_text += "\n\nאיך תרצה להתחיל?"

        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup
        )
        return MAIN_MENU

    @typing_action
    async def handle_message(self, update: Update, context):
        """Handle all text messages with enhanced AI and real-time task management"""
        user = update.effective_user
        message = update.message.text

        # Validate message
        if not validate_user_input(message):
            await update.message.reply_text(
                "מצטערת, ההודעה מכילה תוכן לא תקין. אנא נסה שוב."
            )
            return

        # Register user activity
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
        self.db.register_user(user_data)

        # Send typing indicator for better UX
        await asyncio.sleep(0.3)  # Small delay for natural feeling

        try:
            # Use intelligent agent if available, otherwise fallback to traditional AI
            if self.intelligent_agent:
                # Generate intelligent response using the advanced agent
                intelligent_response = await self.intelligent_agent.process_message(user.id, message)
                ai_response = intelligent_response.content
                
                # Still try to create task if relevant using traditional task manager
                task_result = await self.ai.task_manager.create_and_notify_task(user.id, message)
                
                if task_result:
                    task_message, task_keyboard, task_id = task_result
                    
                    # Combine intelligent response with task creation
                    combined_response = f"""{ai_response}

---

{task_message}"""
                    
                    # Log conversation with task reference
                    self.db.log_conversation(
                        user.id, message, combined_response, 
                        metadata={
                            "task_created": task_id, 
                            "intelligent_agent": True,
                            "confidence": intelligent_response.confidence,
                            "used_tools": intelligent_response.used_tools
                        }
                    )
                    
                    # Send response with task keyboard
                    await update.message.reply_text(
                        combined_response, 
                        reply_markup=task_keyboard,
                        parse_mode='Markdown'
                    )
                    
                    logger.info(f"Task {task_id} created for user {user.id} via intelligent agent")
                else:
                    # Create smart keyboard based on intelligent understanding
                    smart_keyboard = self._create_smart_keyboard_from_intelligent_response(intelligent_response)
                    
                    # Log regular conversation
                    self.db.log_conversation(
                        user.id, message, ai_response,
                        metadata={
                            "intelligent_agent": True,
                            "confidence": intelligent_response.confidence,
                            "used_tools": intelligent_response.used_tools,
                            "emotional_state": intelligent_response.emotional_context.value if intelligent_response.emotional_context else None
                        }
                    )
                    
                    # Send intelligent response
                    await update.message.reply_text(
                        ai_response, 
                        reply_markup=smart_keyboard,
                        parse_mode='Markdown'
                    )
            else:
                # Fallback to traditional AI system
                ai_response, response_keyboard, task_id = await self.ai.generate_response(
                    user_id=user.id,
                    message=message,
                    user_name=user.first_name or "משתמש"
                )

                # Send response with appropriate keyboard
                await update.message.reply_text(
                    ai_response, 
                    reply_markup=response_keyboard,
                    parse_mode='Markdown'
                )

                # If a task was created, send additional confirmation
                if task_id:
                    logger.info(f"Task {task_id} created for user {user.id} via traditional AI")

        except Exception as e:
            logger.error(f"Error handling message from user {user.id}: {e}")
            await update.message.reply_text(
                "😅 מצטערת, קרתה שגיאה קטנה. אני עובדת על תיקון הבעיה.\n"
                "נסה שוב בעוד רגע!"
            )

    def _create_smart_keyboard_from_intelligent_response(self, intelligent_response) -> Optional[InlineKeyboardMarkup]:
        """Create smart keyboard based on intelligent response suggestions"""
        try:
            keyboard = []
            
            # Add suggested actions from the intelligent response
            if intelligent_response.suggestions:
                for i, suggestion in enumerate(intelligent_response.suggestions[:3]):  # Limit to 3 suggestions
                    keyboard.append([InlineKeyboardButton(f"💡 {suggestion[:25]}...", callback_data=f"suggest_{i}")])
            
            # Add emotional support if needed
            if intelligent_response.emotional_context and intelligent_response.emotional_context.value in ['sad', 'frustrated', 'confused']:
                keyboard.append([InlineKeyboardButton("🤗 אני צריך תמיכה", callback_data="emotional_support")])
            
            # Add quick actions
            quick_actions = [
                [InlineKeyboardButton("📋 המשימות שלי", callback_data="my_tasks")],
                [InlineKeyboardButton("❓ עזרה", callback_data="help"), 
                 InlineKeyboardButton("📊 הגדרות", callback_data="settings")]
            ]
            keyboard.extend(quick_actions)
            
            return InlineKeyboardMarkup(keyboard) if keyboard else None
            
        except Exception as e:
            logger.error(f"Error creating smart keyboard: {e}")
            return None

    async def button_handler(self, update: Update, context):
        """Handle inline keyboard callbacks with enhanced task management"""
        query = update.callback_query
        await query.answer()

        data = query.data

        try:
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
                    "פשוט כתוב לי בעברית טבעית! 😊",
                    parse_mode='Markdown'
                )
                return AI_CHAT

            elif data == "my_tasks":
                await self._handle_my_tasks(query)

            elif data.startswith("complete_"):
                await self._handle_complete_task(query, data)

            elif data == "complete_task":
                await self._handle_complete_task_menu(query)

            elif data == "new_task":
                await self._handle_new_task_guide(query)

            elif data == "settings":
                await self._handle_settings(query)

            elif data == "stats":
                await self._handle_stats(query)

            elif data == "help":
                await self._handle_help(query)

            elif data == "main_menu":
                await self._handle_main_menu(query)

            elif data == "continue_chat":
                await query.edit_message_text(
                    "🔄 **המשכנו את השיחה!**\n\n"
                    "שלח לי הודעה וניכנס לשיחה טבעית. אני מוכנה לעזור עם כל נושא! 💬"
                )

            elif data == "urgent_tasks":
                await self._handle_urgent_tasks(query)

            elif data == "overdue_tasks":
                await self._handle_overdue_tasks(query)

            elif data == "task_summary":
                await self._handle_task_summary(query)

            else:
                await query.edit_message_text(
                    "🤔 לא הבנתי את הבחירה. בוא ננסה שוב!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")
                    ]])
                )

        except Exception as e:
            logger.error(f"Error in button handler: {e}")
            await query.edit_message_text(
                "😅 קרתה שגיאה. אני חוזרת לתפריט הראשי.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")
                ]])
            )

    async def _handle_my_tasks(self, query):
        """Handle my tasks display"""
        user_id = query.from_user.id
        user_tasks = self.db.get_user_tasks(user_id)

        if not user_tasks:
            keyboard = [[
                InlineKeyboardButton("➕ צור משימה ראשונה", callback_data="new_task"),
                InlineKeyboardButton("❓ איך זה עובד?", callback_data="help")
            ]]

            await query.edit_message_text(
                "📋 **המשימות שלי**\n\n"
                "אין לך משימות פעילות כרגע.\n\n"
                "💡 **איך יוצרים משימות?**\n"
                "פשוט שלח לי הודעה כמו:\n"
                "• \"תזכור לי לקרוא לרופא מחר\"\n"
                "• \"תקבע פגישה עם הצוות השבוע\"\n"
                "• \"תזכיר לי לשלוח דוח עד יום חמישי\"\n\n"
                "אני אזהה אוטומטית שזו משימה ואצור אותה עבורך! 🤖✨",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return

        # Display tasks
        pending_tasks = [t for t in user_tasks if t.get('status') == 'pending']
        completed_tasks = [t for t in user_tasks if t.get('status') == 'completed']

        tasks_text = f"📋 **המשימות שלי** ({len(pending_tasks)} פעילות)\n\n"

        if pending_tasks:
            tasks_text += "**🟡 פעילות:**\n"
            for i, task in enumerate(pending_tasks[:5], 1):
                category_info = self.ai.task_manager.get_task_category_display(task.get('category', 'other'))
                priority_info = self.ai.task_manager.get_priority_display(task.get('priority', 'medium'))

                title = task['title'][:35] + "..." if len(task['title']) > 35 else task['title']
                tasks_text += f"{i}. {category_info['emoji']} {title}\n"
                tasks_text += f"   {priority_info['emoji']} {priority_info['name']}"

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
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def _handle_complete_task(self, query, data):
        """Handle specific task completion"""
        task_id = data.replace("complete_", "")
        user_id = query.from_user.id

        # Get task from database
        user_tasks = self.db.get_user_tasks(user_id)
        task = next((t for t in user_tasks if t.get('id') == task_id), None)

        if not task:
            await query.edit_message_text(
                "❌ לא מצאתי את המשימה",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")
                ]])
            )
            return

        if task.get('user_id') != user_id:
            await query.edit_message_text("❌ אין לך הרשאה לערוך משימה זו")
            return

        # Complete the task
        success = self.ai.task_manager.complete_task(task_id, user_id)
        
        if success:
            await query.edit_message_text(
                f"🎉 **משימה הושלמה!**\n\n"
                f"✅ {task['title']}\n\n"
                f"כל הכבוד! המשימה סומנה כהושלמה.\n"
                f"⏰ הושלמה: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 למשימות שלי", callback_data="my_tasks"),
                    InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")
                ]]),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ שגיאה בעדכון המשימה. נסה שוב.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")
                ]])
            )

    async def _handle_complete_task_menu(self, query):
        """Show tasks to mark as complete"""
        user_id = query.from_user.id
        user_tasks = self.db.get_user_tasks(user_id, status='pending')

        if not user_tasks:
            await query.edit_message_text(
                "✅ **סימון משימות כהושלמו**\n\n"
                "אין לך משימות פעילות לסימון כרגע.\n"
                "כל הכבוד! נראה שסיימת הכל! 🎉",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")
                ]]),
                parse_mode='Markdown'
            )
            return

        # Create keyboard with tasks to complete
        keyboard = []
        for task in user_tasks[:8]:  # Show max 8 tasks
            title = task['title'][:30] + "..." if len(task['title']) > 30 else task['title']
            keyboard.append([InlineKeyboardButton(
                f"✅ {title}",
                callback_data=f"complete_{task['id']}"
            )])

        keyboard.append([InlineKeyboardButton("⬅️ חזור", callback_data="my_tasks")])

        await query.edit_message_text(
            "✅ **בחר משימה לסימון כהושלמה:**\n\n"
            "לחץ על המשימה שסיימת:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def _handle_new_task_guide(self, query):
        """Show new task creation guide"""
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
            ]]),
            parse_mode='Markdown'
        )

    async def _handle_settings(self, query):
        """Handle settings menu"""
        keyboard = [
            [InlineKeyboardButton("🌐 שפה", callback_data="lang_settings")],
            [InlineKeyboardButton("🔔 התראות", callback_data="notif_settings")],
            [InlineKeyboardButton("🗑️ מחק היסטוריה", callback_data="clear_history")],
            [InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⚙️ **הגדרות מאיה**\n\nבחר את האפשרות שתרצה לערוך:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return SETTINGS_MENU

    async def _handle_stats(self, query):
        """Handle statistics display"""
        stats = self.db.get_basic_stats()
        user_id = query.from_user.id
        task_summary = self.ai.task_manager.get_user_tasks_summary(user_id)

        stats_text = f"""
📊 **סטטיסטיקות הבוט:**

👥 **משתמשים רשומים:** {stats.get('total_users', 0)}
⚡ **פעילים השבוע:** {stats.get('active_users_week', 0)}
💬 **סה"כ שיחות:** {stats.get('total_conversations', 0)}
📈 **שיחות היום:** {stats.get('today_conversations', 0)}

📋 **המשימות שלך:**
🟡 **פעילות:** {task_summary['pending']}
✅ **הושלמו:** {task_summary['completed']}
📈 **סה"כ יצרת:** {task_summary['total']}

🤖 **מצב המערכת:**
🟢 **AI Engine:** {'פעיל' if self.ai.model else 'לא זמין'}
🟢 **Task Manager:** פעיל
🟢 **Database:** {stats.get('database_type', 'Memory')}
🟢 **Status:** {stats.get('uptime', 'Online')}

אני לומדת ומשתפרת מכל שיחה ומשימה! 💜
        """

        keyboard = [[InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(stats_text, reply_markup=reply_markup)

    async def _handle_help(self, query):
        """Handle help display"""
        help_text = """
❓ **מדריך שימוש במאיה**

🎯 **מה אני יכולה לעשות:**
• לענות על שאלות בכל נושא
• ליצור ולנהל משימות חכמות
• לעזור בכתיבה ועריכה
• לתת הסברים על נושאים מורכבים
• לסייע במשימות מזכירות יומיומיות

📋 **ניהול משימות חכם:**
• שלח "תזכור לי..." - ואני אשמור תזכורת
• שלח "תקבע פגישה..." - ואני אארגן פגישה
• שלח "תבדוק..." - ואני אכין משימת מחקר

💡 **טיפים לשימוש:**
• כתוב בעברית טבעית
• תאר בפירוט מה אתה צריך
• אל תהסס לשאול שאלות המשך
• השתמש במילים כמו "דחוף" או "חשוב" לעדיפות

🔧 **פקודות זמינות:**
/start - התחלה מחדש
/tasks - המשימות שלי
/feedback - שליחת משוב

**🌟 הטיפ הכי חשוב:**
פשוט דבר איתי כמו עם מזכירה אמיתית! אני אבין מה אתה צריך 😊
        """

        keyboard = [[InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(help_text, reply_markup=reply_markup)

    async def _handle_main_menu(self, query):
        """Handle main menu display"""
        user_id = query.from_user.id
        task_summary = self.ai.task_manager.get_user_tasks_summary(user_id)

        keyboard = [
            [InlineKeyboardButton("💬 שיחה עם AI", callback_data="ai_chat")],
            [InlineKeyboardButton(
                f"📋 המשימות שלי ({task_summary['pending']})", 
                callback_data="my_tasks"
            )],
            [InlineKeyboardButton("⚙️ הגדרות", callback_data="settings")],
            [InlineKeyboardButton("📊 סטטיסטיקות", callback_data="stats")],
            [InlineKeyboardButton("❓ עזרה", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = "🤖 **מאיה - המזכירה החכמה שלך**\n\n"
        if task_summary['pending'] > 0:
            welcome_text += f"📋 יש לך {task_summary['pending']} משימות פעילות"
            if task_summary['urgent'] > 0:
                welcome_text += f" (כולל {task_summary['urgent']} דחופות! 🔥)"
            welcome_text += "\n\n"
        welcome_text += "מה תרצה לעשות?"

        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return MAIN_MENU

    async def _handle_urgent_tasks(self, query):
        """Handle urgent tasks display"""
        user_id = query.from_user.id
        urgent_tasks = [
            task for task in self.db.get_user_tasks(user_id) 
            if task.get('priority') == 'urgent' and task.get('status') == 'pending'
        ]

        if not urgent_tasks:
            await query.edit_message_text(
                "🔥 **משימות דחופות**\n\n"
                "אין לך משימות דחופות כרגע - מצוין! 😊\n\n"
                "זה אומר שאתה מנהל היטב את הזמן שלך!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 כל המשימות", callback_data="my_tasks"),
                    InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")
                ]]),
                parse_mode='Markdown'
            )
            return

        tasks_text = f"🔥 **משימות דחופות** ({len(urgent_tasks)})\n\n"
        
        for i, task in enumerate(urgent_tasks[:5], 1):
            category_info = self.ai.task_manager.get_task_category_display(task.get('category', 'other'))
            title = task['title'][:40] + "..." if len(task['title']) > 40 else task['title']
            tasks_text += f"{i}. {category_info['emoji']} {title}\n"
            
            if task.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(task['due_date'])
                    tasks_text += f"   📅 {due_date.strftime('%d/%m/%Y')}"
                except:
                    pass
            tasks_text += "\n\n"

        keyboard = [
            [InlineKeyboardButton("✅ סמן הושלם", callback_data="complete_task")],
            [InlineKeyboardButton("📋 כל המשימות", callback_data="my_tasks")],
            [InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")]
        ]

        await query.edit_message_text(
            tasks_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def _handle_overdue_tasks(self, query):
        """Handle overdue tasks display"""
        user_id = query.from_user.id
        user_tasks = self.db.get_user_tasks(user_id, status='pending')
        now = datetime.now()
        
        overdue_tasks = []
        for task in user_tasks:
            if task.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(task['due_date'])
                    if due_date < now:
                        overdue_tasks.append(task)
                except:
                    pass

        if not overdue_tasks:
            await query.edit_message_text(
                "⏰ **משימות באיחור**\n\n"
                "אין לך משימות באיחור - כל הכבוד! 🎉\n\n"
                "אתה עומד בלוחות הזמנים שלך!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 כל המשימות", callback_data="my_tasks"),
                    InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")
                ]]),
                parse_mode='Markdown'
            )
            return

        tasks_text = f"⏰ **משימות באיחור** ({len(overdue_tasks)})\n\n"
        
        for i, task in enumerate(overdue_tasks[:5], 1):
            category_info = self.ai.task_manager.get_task_category_display(task.get('category', 'other'))
            priority_info = self.ai.task_manager.get_priority_display(task.get('priority', 'medium'))
            title = task['title'][:35] + "..." if len(task['title']) > 35 else task['title']
            
            tasks_text += f"{i}. {category_info['emoji']} {title}\n"
            tasks_text += f"   {priority_info['emoji']} {priority_info['name']}"
            
            if task.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(task['due_date'])
                    days_overdue = (now - due_date).days
                    tasks_text += f" | 📅 איחור של {days_overdue} ימים"
                except:
                    pass
            tasks_text += "\n\n"

        keyboard = [
            [InlineKeyboardButton("✅ סמן הושלם", callback_data="complete_task")],
            [InlineKeyboardButton("📋 כל המשימות", callback_data="my_tasks")],
            [InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")]
        ]

        await query.edit_message_text(
            tasks_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def _handle_task_summary(self, query):
        """Handle task summary display"""
        user_id = query.from_user.id
        task_summary = self.ai.task_manager.get_user_tasks_summary(user_id)
        task_stats = self.db.get_task_statistics(user_id)

        summary_text = f"""
📊 **סיכום משימות מפורט**

📈 **סטטיסטיקות כלליות:**
• סה"כ משימות: {task_summary['total']}
• פעילות: {task_summary['pending']} 📋
• הושלמו: {task_summary['completed']} ✅
• בביצוע: {task_summary['in_progress']} 🔄

🚨 **משימות הדורשות תשומת לב:**
• דחופות: {task_summary['urgent']} 🔥
• באיחור: {task_summary['overdue']} ⏰

📋 **פילוח לפי סוגים:**"""

        if task_stats.get('by_category'):
            for category, count in task_stats['by_category'].items():
                category_info = self.ai.task_manager.get_task_category_display(category)
                summary_text += f"\n• {category_info['emoji']} {category_info['name']}: {count}"

        summary_text += f"""

⚡ **פעילות אחרונה:**
• נוצרו היום: {task_stats.get('created_today', 0)}
• הושלמו היום: {task_stats.get('completed_today', 0)}

💡 **הצעה:**"""
        
        if task_summary['urgent'] > 0:
            summary_text += "\nהתמקד תחילה במשימות הדחופות! 🔥"
        elif task_summary['overdue'] > 0:
            summary_text += "\nכדאי לטפל במשימות באיחור 📅"
        elif task_summary['pending'] > 0:
            summary_text += "\nהמשך העבודה הטובה! כל המשימות תחת שליטה 👍"
        else:
            summary_text += "\nנהדר! אין משימות פתוחות - זמן לנוח! 🎉"

        keyboard = [
            [InlineKeyboardButton("📋 למשימות", callback_data="my_tasks")],
            [InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu")]
        ]

        await query.edit_message_text(
            summary_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def tasks_command(self, update: Update, context):
        """Show user tasks with management options"""
        user_id = update.effective_user.id
        user_tasks = self.db.get_user_tasks(user_id)

        if not user_tasks:
            keyboard = [[
                InlineKeyboardButton("➕ צור משימה ראשונה", callback_data="new_task"),
                InlineKeyboardButton("❓ איך זה עובד?", callback_data="help")
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

        # Reuse the tasks display logic
        fake_query = type('MockQuery', (), {
            'from_user': update.effective_user,
            'edit_message_text': update.message.reply_text
        })()
        
        await self._handle_my_tasks(fake_query)

    @admin_only
    async def admin_stats(self, update: Update, context):
        """Enhanced admin statistics with task management data"""
        stats = self.db.get_basic_stats()
        task_stats = self.db.get_task_statistics()  # All users

        admin_text = f"""👑 **פאנל מנהל - סטטיסטיקות מתקדמות**

📊 **נתוני משתמשים:**
• סה"כ משתמשים: {stats.get('total_users', 0)}
• פעילים השבוע: {stats.get('active_users_week', 0)}
• שיחות השבוע: {stats.get('total_conversations', 0)}
• שיחות היום: {stats.get('today_conversations', 0)}

📋 **נתוני משימות (כלל המערכת):**
• סה"כ משימות: {task_stats.get('total', 0)}
• נוצרו היום: {task_stats.get('created_today', 0)}
• הושלמו היום: {task_stats.get('completed_today', 0)}

🤖 **מצב המערכת:**
• AI Engine: {'🟢 פעיל' if self.ai.model else '🔴 לא זמין'}
• Task Manager: 🟢 פעיל
• Database: {f"🟢 {stats.get('database_type', 'Memory')}"}
• Uptime: {stats.get('uptime', 'Online')}

🔧 **פילוח משימות לפי סטטוס:**"""

        if task_stats.get('by_status'):
            for status, count in task_stats['by_status'].items():
                status_emoji = {'pending': '🟡', 'completed': '✅', 'in_progress': '🔄'}.get(status, '📋')
                admin_text += f"\n• {status_emoji} {status}: {count}"

        await update.message.reply_text(admin_text, parse_mode='Markdown')

    @admin_only
    async def broadcast_message(self, update: Update, context):
        """Send message to all users with enhanced reporting"""
        if not context.args:
            await update.message.reply_text(
                "📢 **שידור הודעה לכל המשתמשים**\n\n"
                "שימוש: `/broadcast הודעה לכל המשתמשים`\n\n"
                "הודעה תישלח לכל המשתמשים הרשומים במערכת.",
                parse_mode='Markdown'
            )
            return

        message = " ".join(context.args)
        await update.message.reply_text("📤 מתחיל שידור...")

        try:
            sent_count = 0
            failed_count = 0
            start_time = datetime.now()

            if hasattr(self.db.users, 'find'):  # MongoDB
                async for user in self.db.users.find({"is_active": True}):
                    try:
                        await context.bot.send_message(
                            user["user_id"], 
                            f"📢 **הודעה ממאיה:**\n\n{message}",
                            parse_mode='Markdown'
                        )
                        sent_count += 1
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        failed_count += 1
                        logger.warning(f"Failed to send broadcast to {user['user_id']}: {e}")
            else:  # In-memory
                for user_id, user_data in self.db.users.items():
                    try:
                        await context.bot.send_message(
                            user_id,
                            f"📢 **הודעה ממאיה:**\n\n{message}",
                            parse_mode='Markdown'
                        )
                        sent_count += 1
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        failed_count += 1
                        logger.warning(f"Failed to send broadcast to {user_id}: {e}")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            await update.message.reply_text(
                f"✅ **שידור הושלם!**\n\n"
                f"📤 נשלח בהצלחה: {sent_count}\n"
                f"❌ נכשל: {failed_count}\n"
                f"⏱️ משך זמן: {duration:.1f} שניות\n"
                f"📊 הצלחה: {(sent_count/(sent_count+failed_count)*100):.1f}%",
                parse_mode='Markdown'
            )

        except Exception as e:
            await update.message.reply_text(f"❌ שגיאה בשידור: {e}")

    async def feedback_command(self, update: Update, context):
        """Collect user feedback with enhanced handling"""
        if not context.args:
            await update.message.reply_text(
                "💬 **שליחת משוב**\n\n"
                "שתף אותי במחשבות שלך על השירות:\n"
                "`/feedback הטקסט שלך כאן`\n\n"
                "המשוב שלך עוזר לי להשתפר! 💜",
                parse_mode='Markdown'
            )
            return

        feedback = " ".join(context.args)
        user = update.effective_user

        # Save feedback to database
        feedback_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }

        # If admin exists, forward feedback
        if ADMIN_ID:
            try:
                await context.bot.send_message(
                    ADMIN_ID,
                    f"📝 **משוב חדש מ-{user.first_name}** ({user.id})\n\n"
                    f"**תוכן:** {feedback}\n\n"
                    f"**זמן:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to forward feedback to admin: {e}")

        await update.message.reply_text(
            "🙏 **תודה על המשוב!**\n\n"
            "המשוב שלך חשוב לי מאוד ויעזור לי להשתפר. "
            "אמשיך להתפתח ולהיות טובה יותר בעזרתך! 💜\n\n"
            "אם יש לך עוד הצעות או שאלות - אני תמיד כאן! 😊",
            parse_mode='Markdown'
        )
# ============================
# MAIN APPLICATION
# ============================

async def error_handler(update: Update, context):
    """Enhanced error handler with detailed logging"""
    logger.error(f"Error occurred: {context.error}")
    logger.error(f"Update: {update}")
    
    # Try to notify user if possible
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "😅 אופס! משהו השתבש. אני עובדת על תיקון הבעיה.\n"
                "נסה שוב בעוד רגע או פנה למנהל אם הבעיה נמשכת.\n\n"
                f"🔧 קוד שגיאה: {str(context.error)[:50]}...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 תפריט ראשי", callback_data="main_menu"),
                    InlineKeyboardButton("💬 צור קשר", callback_data="help")
                ]])
            )
    except Exception as e:
        logger.error(f"Failed to send error message to user: {e}")

    # Notify admin if available
    if ADMIN_ID:
        try:
            user_info = "לא זמין"
            if update and update.effective_user:
                user_info = f"{update.effective_user.first_name} ({update.effective_user.id})"
            
            error_msg = (
                f"🚨 **שגיאה במערכת**\n\n"
                f"**שגיאה:** `{str(context.error)}`\n"
                f"**משתמש:** {user_info}\n"
                f"**זמן:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"**Update Type:** {type(update).__name__ if update else 'None'}"
            )
            
            # Try to get the bot instance for admin notification
            bot = context.bot if context else None
            if bot:
                await bot.send_message(ADMIN_ID, error_msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to notify admin about error: {e}")

def main():
    """Main function to run the bot with enhanced initialization"""
    print("🚀 Starting Maya AI Bot...")
    print("=" * 50)
    
    # Validate required environment variables
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN is required!")
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable is missing!")
        print("Please set your Telegram bot token and try again.")
        return

    if not GEMINI_API_KEY:
        logger.warning("⚠️ GEMINI_API_KEY is not set, using basic AI features only")
        print("⚠️ Warning: GEMINI_API_KEY not found - AI features will be limited")

    if not MONGO_URI:
        logger.warning("⚠️ MONGO_URI is not set, using in-memory storage")
        print("⚠️ Warning: MONGO_URI not found - using in-memory storage")

    try:
        # Start Flask server for keep-alive
        logger.info("🚀 Starting Keep-Alive server...")
        print("🚀 Starting Keep-Alive server...")
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()

        # Initialize bot
        logger.info("🤖 Initializing Maya AI Bot...")
        print("🤖 Initializing Maya AI Bot...")
        maya = MayaBot()

        # Test database connection
        if hasattr(maya.db.users, 'find'):
            print("✅ MongoDB connection established")
        else:
            print("⚠️ Using in-memory storage")

        # Test AI model
        if maya.ai.model:
            print("✅ Gemini AI model initialized")
        else:
            print("⚠️ AI model not available - using fallback responses")

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
            ],
            per_chat=True,
            per_user=True
        )

        # Add handlers in priority order
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("admin_stats", maya.admin_stats))
        application.add_handler(CommandHandler("broadcast", maya.broadcast_message))
        application.add_handler(CommandHandler("feedback", maya.feedback_command))
        application.add_handler(CommandHandler("tasks", maya.tasks_command))

        # Fallback handler for any text message not caught by conversation handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, maya.handle_message))

        # Handle callback queries not caught by conversation handler
        application.add_handler(CallbackQueryHandler(maya.button_handler))

        # Add error handler
        application.add_error_handler(error_handler)

        # Print startup information
        print("=" * 50)
        print("✅ Maya Bot Configuration:")
        print(f"   • Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
        print(f"   • Gemini AI: {'✅ Active' if GEMINI_API_KEY else '⚠️ Disabled'}")
        print(f"   • Database: {'✅ MongoDB' if MONGO_URI else '⚠️ Memory'}")
        print(f"   • Admin ID: {'✅ Set' if ADMIN_ID else '⚠️ Not Set'}")
        print(f"   • Flask Port: {os.environ.get('PORT', 5000)}")
        print("=" * 50)

        # Start the bot
        logger.info("✅ Maya is starting up...")
        print("✅ Maya is starting up...")
        print("📡 Bot will be available soon...")
        print("🔄 Press Ctrl+C to stop the bot")
        print("=" * 50)

        # Run bot with polling
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )

    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("⏹️ Bot stopped by user")
        print("👋 Thanks for using Maya!")
        print("=" * 50)
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        print(f"❌ Critical Error: {e}")
        print("Please check your configuration and try again.")
    finally:
        # Cleanup
        try:
            if 'maya' in locals():
                # Close database connections
                if hasattr(maya.db, '__del__'):
                    maya.db.__del__()
        except:
            pass

def health_check():
    """Standalone health check function"""
    try:
        # Test basic functionality
        db = DatabaseManager()
        stats = db.get_basic_stats()
        
        print("🏥 Health Check Results:")
        print(f"   • Database: {'✅ OK' if not stats.get('error') else '❌ Error'}")
        print(f"   • Total Users: {stats.get('total_users', 0)}")
        print(f"   • Bot Status: ✅ Healthy")
        return True
    except Exception as e:
        print(f"🏥 Health Check Failed: {e}")
        return False

if __name__ == '__main__':
    # Add command line argument support
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'health':
            health_check()
            sys.exit(0)
        elif sys.argv[1] == 'test':
            print("🧪 Running basic tests...")
            
            # Test imports
            try:
                maya = MayaBot()
                print("✅ Bot initialization: OK")
            except Exception as e:
                print(f"❌ Bot initialization: {e}")
                sys.exit(1)
            
            # Test database
            try:
                stats = maya.db.get_basic_stats()
                print("✅ Database connection: OK")
            except Exception as e:
                print(f"❌ Database connection: {e}")
                sys.exit(1)
            
            # Test task manager
            try:
                intent = maya.ai.task_manager.analyze_user_intent("תזכור לי משהו")
                print(f"✅ Task manager: OK (detected: {intent})")
            except Exception as e:
                print(f"❌ Task manager: {e}")
                sys.exit(1)
            
            print("🎉 All tests passed!")
            sys.exit(0)
        elif sys.argv[1] == 'version':
            print("Maya AI Bot v2.1")
            print("Enhanced with task management and Hebrew support")
            sys.exit(0)
        else:
            print("Usage:")
            print("  python maya_bot.py          # Run the bot")
            print("  python maya_bot.py health   # Health check")
            print("  python maya_bot.py test     # Run tests")
            print("  python maya_bot.py version  # Show version")
            sys.exit(0)
    
    # Normal startup
    main()
        


               
      
