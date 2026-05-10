import asyncio

from concurrent.futures import (
    ThreadPoolExecutor
)

from ai_gateway import (
    AIGateway
)


class AsyncAI:

    def __init__(self):

        self.ai = AIGateway()

        self.pool = ThreadPoolExecutor(
            max_workers=4
        )

    async def generate(

        self,

        prompt

    ):

        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(

            self.pool,

            self.ai.generate,

            prompt

        )
