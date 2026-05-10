import asyncio

class TaskQueue:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def add_task(self, user_id: int, task: str):
        await self.queue.put((user_id, task))

    async def get_task(self):
        return await self.queue.get()
