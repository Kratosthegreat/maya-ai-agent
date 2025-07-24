def _create_context_keyboard(self, message: str, user_id: int, intent=None) -> InlineKeyboardMarkup:
        """Create smart context-aware keyboard"""
        keyboard = []
        
        # Task-related buttons if intent detected
        if intent and intent[0] in ['reminder', 'meeting', 'schedule', 'email', 'research']:
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
            return "זו שאלה מעניינת! כרגע אני עסוקה, אבל חזור אליי בעודרגע ואתן לך תשובה מפורטת 🤔"
        
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
        
        # Register user activity
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
        self.db.register_user(user_data)
        
        # Send typing indicator for better UX
        await asyncio.sleep(0.5)  # Small delay for natural feeling
        
        # Generate AI response with enhanced task management
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
            logger.info(f"Task {task_id} created for user {user.id}")
    
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
            user_tasks = [task for task in self.db.tasks.values() if task.get('user_id') == user_id]
            
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
            
            if pending_tasks:
                tasks_text += "**🟡 פעילות:**\n"
                for i, task in enumerate(pending_tasks[:5], 1):
                    category_info = self.ai.task_manager.get_task_category_display(task.get('category', 'other'))
                    priority_info = self.ai.task_manager.get_priority_display(task.get('priority', 'medium'))
                    
                    tasks_text += f"{i}. {category_info['emoji']} {task['title'][:35]}...\n"
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
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data.startswith("complete_"):
            # Mark specific task as complete
            task_id = data.replace("complete_", "")
            
            if task_id in self.db.tasks:
                task = self.db.tasks[task_id]
                
                if task.get('user_id') != query.from_user.id:
                    await query.edit_message_text("❌ אין לך הרשאה לערוך משימה זו")
                    return
                
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                task['updated_at'] = datetime.now().isoformat()
                
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
                    "❌ לא מצאתי את המשימה",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")
                    ]])
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
        
        elif data == "main_menu":
            # Enhanced main menu with task info
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
                reply_markup=reply_markup
            )
            return MAIN_MENU
        
        # Add more handlers as needed...
        elif data == "stats":
            # Enhanced stats with task information
            stats = self.db.get_basic_stats()
            
            # Add task stats
            user_id = query.from_user.id
            task_summary = self.ai.task_manager.get_user_tasks_summary(user_id)
            
            stats_text = f"""
📊 **סטטיסטיקות הבוט:**

👥 **משתמשים רשומים:** {stats.get('total_users', 0)}
⚡ **פעילים השבוע:** {stats.get('active_users_week', 0)}
💬 **סה"כ שיחות:** {stats.get('total_conversations', 0)}

📋 **המשימות שלך:**
🟡 **פעילות:** {task_summary['pending']}
✅ **הושלמו:** {task_summary['completed']}
📈 **סה"כ יצרת:** {task_summary['total']}

🤖 **מצב המערכת:**
🟢 **AI Engine:** פעיל
🟢 **Task Manager:** פעיל
🟢 **Status:** {stats.get('uptime', 'Online')}

אני לומדת ומשתפרת מכל שיחה ומשימה! 💜
            """
            
            keyboard = [[InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(stats_text, reply_markup=reply_markup)
    
    async def tasks_command(self, update: Update, context):
        """Show user tasks with management options"""
        user_id = update.effective_user.id
        user_tasks = [task for task in self.db.tasks.values() if task.get('user_id') == user_id]
        
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
                "• \"תקבע פגישה עם הצוות השבוع\"\n"
                "• \"תזכיר לי לשלוח דוח עד יום חמישי\"",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Create detailed task display
        await self.button_handler(update, context)  # Reuse the button handler logic
    
    @admin_only
    async def admin_stats(self, update: Update, context):
        """Enhanced admin statistics with task management data"""
        stats = self.db.get_basic_stats()
        task_stats = self.db.get_task_statistics()  # All users
        
        # Additional admin-only stats
        admin_text = f"""👑 **פאנל מנהל - סטטיסטיקות מתקדמות**

📊 **נתוני משתמשים:**
• סה"כ משתמשים: {stats.get('total_users', 0)}
• פעילים השבוע: {stats.get('active_users_week', 0)}
• שיחות השבוע: {stats.get('total_conversations', 0)}

📋 **נתוני משימות (כלל המערכת):**
• סה"כ משימות: {task_stats.get('total', 0)}
• נוצרו היום: {task_stats.get('created_today', 0)}
• הושלמו היום: {task_stats.get('completed_today', 0)}

🤖 **מצב המערכת:**
• AI Engine: {'🟢 פעיל' if self.ai.model else '🔴 לא זמין'}
• Task Manager: {'🟢 פעיל' if hasattr(self.db, 'tasks') else '🟡 בסיסי'}
• Database: {'🟢 MongoDB' if hasattr(self.db.users, 'find') else '🟡 זיכרון'}
• Uptime: {stats.get('uptime', 'Online')}
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
    application.add_handler(CommandHandler("tasks", maya.tasks_command))
    
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
    logger.info("📡 Bot will be available soon...")
    
    try:
        # Run bot with polling
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")

if __name__ == '__main__':
    main()#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        self.tasks = {}  # Initialize tasks storage
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
                        message_type: str = "text", metadata: str = None) -> bool:
        """Enhanced conversation logging with metadata support"""
        try:
            conversation_data = {
                "user_id": user_id,
                "timestamp": datetime.now(),
                "user_message": message,
                "bot_response": response,
                "message_type": message_type,
                "response_length": len(response),
                "ai_model": "gemini-pro",
                "metadata": metadata  # For task_id references, etc.
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
    
    def get_task_statistics(self, user_id: int = None) -> Dict:
        """Get comprehensive task statistics"""
        try:
            if not hasattr(self, 'tasks'):
                return {'error': 'No task system available'}
            
            all_tasks = list(self.tasks.values())
            
            if user_id:
                all_tasks = [task for task in all_tasks if task.get('user_id') == user_id]
            
            if not all_tasks:
                return {'total': 0, 'by_status': {}, 'by_category': {}, 'by_priority': {}}
            
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
            date = datetime.fromisoformat(date_string)
            today = datetime.now().date()
            return date.date() == today
        except:
            return False

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
        self.db.tasks[task_id] = task_details
        
        logger.info(f"Task created: {task_id} - {task_details['title']}")
        return task_id
    
    def get_task_category_display(self, category: str) -> Dict:
        """Get formatted category with emoji and metadata"""
        category_map = {
            'reminder': {'emoji': '⏰', 'name': 'תזכורת', 'color': 'blue'},
            'meeting': {'emoji': '🤝', 'name': 'פגישה', 'color': 'green'},
            'schedule': {'emoji': '📅', 'name': 'לוח זמנים', 'color': 'purple'},
            'email': {'emoji': '📧', 'name': 'אימייל', 'color': 'red'},
            'research': {'emoji': '🔍', 'name': 'מחקר', 'color': 'orange'},
            'call': {'emoji': '📞', 'name': 'שיחה', 'color': 'cyan'},
            'document': {'emoji': '📄', 'name': 'מסמך', 'color': 'gray'}
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
    
    async def create_and_notify_task(self, user_id: int, message: str) -> Optional[tuple]:
        """Create task and return with interactive keyboard"""
        intent_result = self.analyze_user_intent(message)
        
        if not intent_result:
            return None
        
        intent, confidence = intent_result
        
        if confidence >= 1 and intent in ['reminder', 'meeting', 'schedule', 'email', 'research']:
            task_details = self.extract_task_details(message)
            task_details['user_id'] = user_id
            task_details['created_by_ai'] = True
            
            # Save task
            task_id = self._save_task(task_details)
            
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
        user_tasks = [task for task in self.db.tasks.values() if task.get('user_id') == user_id]
        
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
    
    async def generate_response(self, user_id: int, message: str, 
                              user_name: str = "משתמש") -> tuple:
        """Generate intelligent response with enhanced task management"""
        try:
            if not self.model:
                return self._fallback_response(message), None, None
            
            # Analyze user intent first
            intent = self.task_manager.analyze_user_intent(message)
            
            # Get user task summary for context
            task_summary = self.task_manager.get_user_tasks_summary(user_id)
            
            # Build rich context with task awareness
            context = await self.build_rich_context(user_id, message, intent, task_summary)
            
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
                self.db.log_conversation(user_id, message, combined_response, f"task_created:{task_id}")
                
                return combined_response, task_keyboard, task_id
            else:
                # No task created, return regular response with smart keyboard
                smart_keyboard = self._create_context_keyboard(message, user_id, intent)
                
                # Log regular conversation
                self.db.log_conversation(user_id, message, ai_response)
                
                return ai_response, smart_keyboard, None
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._fallback_response(message), None, None
    
    async def build_rich_context(self, user_id: int, message: str, intent=None, task_summary=None) -> str:
        """Build comprehensive context with task and user awareness"""
        # Get conversation history
        context = self.db.get_user_context(user_id, last_n=3)
        
        # Get recent tasks
        user_tasks = [task for task in self.db.tasks.values() if task.get('user_id') == user_id]
        user_tasks = sorted(user_tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        # Build context string
        context_str = ""
        if context:
            context_str = "\n\nהיסטוריית השיחה האחרונה:\n"
            for i, conv in enumerate(reversed(context), 1):
                context_str += f"{i}. משתמש: {conv['user_message']}\n"
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
            summary_str = f"\n\nסיכום משימות:"
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
            if intent[0] in ['reminder', 'meeting', 'schedule']:
                intent_str += "\n(הכן ליצור משימה אוטומטית)"
        
        return f"""
{MAYA_PERSONALITY}

כמזכירה אישית חכמה ואקטיבית, תפקידי הוא:
- להבין כוונות ולזהות משימות אוטומטית
- לנהל משימות ותזכורות בצורה פרואקטיבית
- לספק מעקב ועדכונים על התקדמות
- להיות זמינה ומגיבה לצרכים משתנים

{context_str}{tasks_str}{summary_str}{intent_str}

ההודעה הנוכחית: "{message}"

הגב בעברית טבעית וידידותית. 
אם זיהיתי כוונה למשימה - הסבר מה אני עושה.
התייחס למשימות קיימות ולהיסטוריה אם רלוונטי.
תן עצות פרואקטיביות לניהול זמן וארגון.
"""
    
    def _create_context_keyboard(self, message: str, user_id: int, intent=None) -> InlineKeyboardMarkup:
        """Create smart context-aware keyboard"""
        keyboard = []
        
        # Task-related buttons if intent detected
        if intent and intent[0] in ['reminder', 'meeting', 'schedule', 'email', 'research']:
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
            return "אני מזכירה אישית חכמה! כרגע יש לי בעיה טכנית קטנה, אبل בקרוב אוכל לעזור לך עם משימות ותזכורות! 🗓️"
        
        # Regular fallbacks
        if any(word in message_lower for word in ["שלום", "היי", "מה נשמע"]):
            return f"שלום! אני מאיה, המזכירה האישית החכמה שלך! איך אוכל לעזור? 😊\n\nאני יכולה לעזור עם תزכורות, פגישות, מחקר ועוד!"
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
- שיחות טבעיות בעברית
- יצירת וניהול משימות חכמות
- תזכורות ותזמון פגישות
- עזרה במשימות יומיומיות
- למידה מכל שיחה שלנו"""
        
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
        
        # Register user activity
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
        self.db.register_user(user_data)
        
        # Send typing indicator for better UX
        await asyncio.sleep(0.5)  # Small delay for natural feeling
        
        # Generate AI response with enhanced task management
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
            logger.info(f"Task {task_id} created for user {user.id}")
    
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
            user_tasks = [task for task in self.db.tasks.values() if task.get('user_id') == user_id]
            
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
            
            if pending_tasks:
                tasks_text += "**🟡 פעילות:**\n"
                for i, task in enumerate(pending_tasks[:5], 1):
                    category_info = self.ai.task_manager.get_task_category_display(task.get('category', 'other'))
                    priority_info = self.ai.task_manager.get_priority_display(task.get('priority', 'medium'))
                    
                    tasks_text += f"{i}. {category_info['emoji']} {task['title'][:35]}...\n"
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
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data.startswith("complete_"):
            # Mark specific task as complete
            task_id = data.replace("complete_", "")
            
            if task_id in self.db.tasks:
                task = self.db.tasks[task_id]
                
                if task.get('user_id') != query.from_user.id:
                    await query.edit_message_text("❌ אין לך הרשאה לערוך משימה זו")
                    return
                
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                task['updated_at'] = datetime.now().isoformat()
                
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
                    "❌ לא מצאתי את המשימה",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ חזור למשימות", callback_data="my_tasks")
                    ]])
                )
        
        elif data == "complete_task":
            # Show tasks to mark as complete
            user_id = query.from_user.id
            user_tasks = [task for task in self.db.tasks.values() 
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
            # Enhanced stats with task information
            stats = self.db.get_basic_stats()
            
            # Add task stats
            user_id = query.from_user.id
            task_summary = self.ai.task_manager.get_user_tasks_summary(user_id)
            
            stats_text = f"""
📊 **סטטיסטיקות הבוט:**

👥 **משתמשים רשומים:** {stats.get('total_users', 0)}
⚡ **פעילים השבוע:** {stats.get('active_users_week', 0)}
💬 **סה"כ שיחות:** {stats.get('total_conversations', 0)}

📋 **המשימות שלך:**
🟡 **פעילות:** {task_summary['pending']}
✅ **הושלמו:** {task_summary['completed']}
📈 **סה"כ יצרת:** {task_summary['total']}

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
- לענות על שאלות בכל נושא
- ליצור ולנהל משימות חכמות
- לעזור בכתיבה ועריכה
- לתת הסברים על נושאים מורכבים
- לסייע במשימות מזכירות יומיומיות

📋 **ניהול משימות חכם:**
- שלח "תזכור לי..." - ואני אשמור תזכורת
- שלח "תקבע פגישה..." - ואני אארגן פגישה
- שלח "תבדוק..." - ואני אכין משימת מחקר

💡 **טיפים לשימוש:**
- כתוב בעברית טבעית
- תאר בפירוט מה אתה צריך
- אל תהסס לשאול שאלות המשך

🔧 **פקודות זמינות:**
/start - התחלה מחדש
/tasks - המשימות שלי
/feedback - שליחת משוב
            """
            
            keyboard = [[InlineKeyboardButton("⬅️ חזור", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(help_text, reply_markup=reply_markup)
        
        elif data == "main_menu":
            # Enhanced main menu with task info
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
                reply_markup=reply_markup
            )
            return MAIN_MENU
    
    async def tasks_command(self, update: Update, context):
        """Show user tasks with management options"""
        user_id = update.effective_user.id
        user_tasks = [task for task in self.db.tasks.values() if task.get('user_id') == user_id]
        
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
        
        # Create detailed task display  
        await self.button_handler(update, context)  # Reuse the button handler logic
    
    @admin_only
    async def admin_stats(self, update: Update, context):
        """Enhanced admin statistics with task management data"""
        stats = self.db.get_basic_stats()
        task_stats = self.db.get_task_statistics()  # All users
        
        # Additional admin-only stats
        admin_text = f"""👑 **פאנל מנהל - סטטיסטיקות מתקדמות**

📊 **נתוני משתמשים:**
- סה"כ משתמשים: {stats.get('total_users', 0)}
- פעילים השבוע: {stats.get('active_users_week', 0)}
- שיחות השבוע: {stats.get('total_conversations', 0)}

📋 **נתוני משימות (כלל המערכת):**
- סה"כ משימות: {task_stats.get('total', 0)}
- נוצרו היום: {task_stats.get('created_today', 0)}
- הושלמו היום: {task_stats.get('completed_today', 0)}

🤖 **מצב המערכת:**
- AI Engine: {'🟢 פעיל' if self.ai.model else '🔴 לא זמין'}
- Task Manager: {'🟢 פעיל' if hasattr(self.db, 'tasks') else '🟡 בסיסי'}
- Database: {'🟢 MongoDB' if hasattr(self.db.users, 'find') else '🟡 זיכרון'}
- Uptime: {stats.get('uptime', 'Online')}
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
        
        # If admin exists, forward feedback
        if ADMIN_ID:
            try:
                await context.bot.send_message(
                    ADMIN_ID,
                    f" 📝 משוב חדש מ-{user.first_name} ({user.id}):\n\n{feedback}"
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
   application.add_handler(CommandHandler("tasks", maya.tasks_command))
   
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
   logger.info("📡 Bot will be available soon...")
   
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
