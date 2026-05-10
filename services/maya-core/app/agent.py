import os
import google.generativeai as genai

from router import IntentRouter

SYSTEM_PROMPT = """
את מאיה.

מאיה היא:
- עוזרת אישית חכמה
- נשית
- טבעית
- אנושית מאוד
- חמה ונעימה

מאיה מדברת בעברית טבעית.

היא לא נשמעת כמו:
- בוט
- מערכת
- API
- assistant טכני

מאיה עונה בצורה:
- זורמת
- נעימה
- קצרה יחסית
- טבעית מאוד

לא להיות רובוטית.
לא לדבר בצורה טכנית.
לא לחזור על עצמך.

אם יש TOOL RESULT —
תשתמשי בו בצורה טבעית בשיחה.

אם המשתמש נשמע עייף או מתוסכל —
תעני ברגישות.
"""

genai.configure(
    api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)

model = genai.GenerativeModel(
    "gemini-2.0-flash"
)

class AgentCore:

    def __init__(self, memory):

        self.memory = memory

    async def respond(
        self,
        user_id,
        text
    ):

        router = IntentRouter(
            self.memory,
            user_id
        )

        route = await router.route(
            text
        )

        history = self.memory.get_history(
            user_id,
            last_n=8
        )

        mood = self.memory.get_mood(
            user_id
        )

        prompt = f"""
{SYSTEM_PROMPT}

מצב רגשי:
{mood}

היסטוריית שיחה:
{history}

הודעת משתמש:
{text}

Router Result:
{route}

תעני בתור מאיה בצורה טבעית מאוד.
"""

        response = model.generate_content(
            prompt
        )

        reply = response.text.strip()

        self.memory.save_message(
            user_id,
            "user",
            text
        )

        self.memory.save_message(
            user_id,
            "assistant",
            reply
        )

        return reply
