

from core.control_plane import (
    MayaControlPlane
)

import asyncio
import logging
import threading

from flask import Flask

from telegram import Update

from telegram.ext import (

    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes

)

from config import (
    TELEGRAM_TOKEN
)

from monitor import (
    SystemMonitor
)

from agent_kernel import (
    MayaKernel
)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app_flask = Flask(__name__)



kernel = MayaKernel()

control_plane = MayaControlPlane(
    kernel.actions
)




@app_flask.route("/")
def health():

    return "Maya V5 online"


async def handle_message(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    text = update.message.text

    response = await kernel.execute(
        text
    )

    await update.message.reply_text(
        response[:4000]
    )


def run_flask():

    app_flask.run(

        host="0.0.0.0",

        port=5000

    )


####################################
# THREAD HELPERS
####################################

def start_monitor_thread():

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    

monitor = SystemMonitor(
    control_plane
)



    loop.run_until_complete(
        monitor.start()
    )


def start_kernel_thread():

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        kernel.autonomous_loop()
    )


####################################
# MAIN
####################################

def main():

    logger.info(
        "🚀 Maya V5 starting..."
    )

    ################################
    # Flask
    ################################

    flask_thread = threading.Thread(

        target=run_flask,

        daemon=True

    )

    flask_thread.start()

    ################################
    # Monitor
    ################################

    threading.Thread(

        target=start_monitor_thread,

        daemon=True

    ).start()

    ################################
    # Autonomous Kernel
    ################################

    threading.Thread(

        target=start_kernel_thread,

        daemon=True

    ).start()

    ################################
    # Telegram
    ################################

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    app.add_handler(

        MessageHandler(

            filters.TEXT,

            handle_message

        )

    )

    logger.info(
        "✅ Maya Kernel active"
    )

    logger.info(
        "✅ Autonomous loop active"
    )

    logger.info(
        "✅ Monitor active"
    )

    logger.info(
        "✅ Telegram polling started"
    )

    app.run_polling()


if __name__ == "__main__":

    main()
