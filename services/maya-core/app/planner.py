import logging
import asyncio

logger = logging.getLogger(__name__)

class Planner:
    def __init__(self, model):
        self.model = model

    async def plan(self, goal: str) -> list:
        prompt = f"""
את מערכת תכנון.

המטרה:
{goal}

תפרק את זה לצעדים.

פורמט:
STEP: פעולה
STEP: פעולה
"""

        try:
            result = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )

            text = result.text.strip()

            steps = [
                line.replace("STEP:", "").strip()
                for line in text.splitlines()
                if line.startswith("STEP:")
            ]

            return steps[:5]

        except Exception as e:
            logger.error(f"Planner error: {e}")
            return []
