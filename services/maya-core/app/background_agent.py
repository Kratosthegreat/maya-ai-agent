import asyncio
import logging

logger = logging.getLogger(__name__)

class BackgroundAgent:
    def __init__(self, agent_loop, planner, queue):
        self.agent_loop = agent_loop
        self.planner = planner
        self.queue = queue

    async def start(self):
        logger.info("🚀 BackgroundAgent started")

        while True:
            user_id, task = await self.queue.get_task()

            logger.info(f"[BG] New task: {task}")

            steps = await self.planner.plan(task)

            for step in steps:
                logger.info(f"[BG] Step: {step}")

                try:
                    await self.agent_loop.run(step)
                except Exception as e:
                    logger.error(f"Step failed: {e}")

            await asyncio.sleep(1)
