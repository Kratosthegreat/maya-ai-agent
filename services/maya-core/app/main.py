import asyncio
import logging

from memory import Memory
from reminders import ReminderEngine
from monitor import SystemMonitor

from telegram.ext import (
    ApplicationBuilder
)

from config import (
    TELEGRAM_TOKEN
)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


async def main():

    logger.info(
        "🚀 Maya starting..."
    )

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    memory = Memory()

    reminder_engine = ReminderEngine(
        app.bot,
        memory
    )

    reminder_engine.start()

    logger.info(
        "✅ ReminderEngine running"
    )

    monitor = SystemMonitor()

    asyncio.create_task(
        monitor.start()
    )

    logger.info(
        "✅ SystemMonitor running"
    )

    await app.initialize()

    await app.start()

    logger.info(
        "✅ Telegram bot running"
    )

    while True:

        await asyncio.sleep(60)


if __name__ == "__main__":

    asyncio.run(main())
