"""Proactive reminder engine — checks every minute and sends Telegram alerts."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class ReminderEngine:
    def __init__(self, bot, memory):
        self.bot       = bot
        self.mem       = memory
        self.scheduler = AsyncIOScheduler(timezone="Asia/Jerusalem")

    def start(self):
        self.scheduler.add_job(
            self._check,
            trigger="interval",
            minutes=1,
            id="reminder_check",
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("✅ ReminderEngine started")

    async def _check(self):
        try:
            due_tasks = self.mem.get_due_tasks()
            for task in due_tasks:
                uid   = task.get("user_id")
                title = task.get("title", "משימה")
                tid   = task.get("id")
                if not uid:
                    continue
                await self.bot.send_message(
                    chat_id=uid,
                    text=f"⏰ *תזכורת!*\n\n📌 {title}",
                    parse_mode="Markdown"
                )
                self.mem.mark_reminded(tid)
                logger.info(f"Reminder sent: {tid} → {uid}")
        except Exception as e:
            logger.error(f"ReminderEngine error: {e}")
