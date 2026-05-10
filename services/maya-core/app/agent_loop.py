import logging
import asyncio
from typing import Dict, Any

from tools import ToolExecutor

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
את מאיה — עוזרת אישית חכמה.

השם שלך הוא מאיה.
את נקבה.

אם אפשר לענות ישירות —
תחזירי FINAL מיד.

תשתמשי ב-ACTION רק כשבאמת צריך כלי.
"""

class AgentLoop:

    def __init__(self, model, memory, user_id):

        self.model = model
        self.memory = memory
        self.user_id = user_id
        self.executor = ToolExecutor(memory, user_id)

    async def run(self, user_input: str) -> str:

        # 🔥 FAST PATH
        simple_inputs = [
            "היי",
            "שלום",
            "מה נשמע",
            "מי את",
            "איך קוראים לך"
        ]

        if user_input.lower() in simple_inputs:

            return "היי 😊 אני מאיה."

        prompt = self._build_prompt(user_input)

        try:

            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    prompt
                ),
                timeout=20
            )

            text = result.text.strip()

            parsed = self._parse(text)

            if parsed["type"] == "final":
                return parsed["content"]

            if parsed["type"] == "action":

                tool_name = parsed["tool"]
                args = parsed.get("args", {})

                tool_result = self.executor.run(
                    tool_name,
                    args
                )

                followup_prompt = f"""
המשתמש ביקש:
{user_input}

הכלי {tool_name} החזיר:
{tool_result}

תעני למשתמש תשובה סופית.

פורמט:
FINAL: תשובה
"""

                followup = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.model.generate_content,
                        followup_prompt
                    ),
                    timeout=20
                )

                final_text = followup.text.strip()

                if final_text.startswith("FINAL:"):
                    return final_text.replace("FINAL:", "").strip()

                return final_text

            return text

        except asyncio.TimeoutError:

            logger.error("LLM timeout")

            return "המערכת איטית כרגע, נסה שוב בעוד רגע."

        except Exception as e:

            logger.exception(f"AgentLoop error: {e}")

            return "אירעה שגיאה פנימית."

    def _build_prompt(self, user_input: str):

        return f"""
{SYSTEM_PROMPT}

משתמש:
{user_input}

אם צריך כלי:
ACTION: tool_name {{}}

אחרת:
FINAL: תשובה
"""

    def _parse(self, text: str) -> Dict:

        if text.startswith("FINAL:"):

            return {
                "type": "final",
                "content": text.replace(
                    "FINAL:",
                    ""
                ).strip()
            }

        if text.startswith("ACTION:"):

            import json

            try:

                parts = text.replace(
                    "ACTION:",
                    ""
                ).strip().split(" ", 1)

                tool = parts[0]

                args = {}

                if len(parts) > 1:
                    args = json.loads(parts[1])

                return {
                    "type": "action",
                    "tool": tool,
                    "args": args
                }

            except Exception:

                return {
                    "type": "unknown"
                }

        return {
            "type": "unknown"
        }
