from tools import ToolExecutor

class IntentRouter:

    def __init__(self, memory, user_id):

        self.memory = memory

        self.user_id = user_id

        self.tools = ToolExecutor(
            memory,
            user_id
        )

    async def route(
        self,
        text: str
    ):

        lowered = text.lower().strip()

        result = {
            "intent": "chat",
            "tool_result": None,
            "memory": {}
        }

        # ─────────────────────────
        # MOOD DETECTION
        # ─────────────────────────

        sad_keywords = [
            "עייף",
            "קשה לי",
            "מבואס",
            "לחוץ",
            "עצוב",
            "מתוסכל"
        ]

        happy_keywords = [
            "שמח",
            "רגוע",
            "איזה כיף",
            "מרוצה"
        ]

        for word in sad_keywords:

            if word in lowered:

                self.memory.set_mood(
                    self.user_id,
                    "sad"
                )

                result["memory"][
                    "mood"
                ] = "sad"

                return result

        for word in happy_keywords:

            if word in lowered:

                self.memory.set_mood(
                    self.user_id,
                    "happy"
                )

                result["memory"][
                    "mood"
                ] = "happy"

                return result

        # ─────────────────────────
        # TIME
        # ─────────────────────────

        if "שעה" in lowered:

            result["intent"] = "time"

            result["tool_result"] = self.tools.run(
                "get_time",
                {}
            )

            return result

        # ─────────────────────────
        # DATE
        # ─────────────────────────

        if "תאריך" in lowered:

            result["intent"] = "date"

            result["tool_result"] = self.tools.run(
                "get_date",
                {}
            )

            return result

        # ─────────────────────────
        # YEAR
        # ─────────────────────────

        if "שנה" in lowered:

            result["intent"] = "year"

            result["tool_result"] = self.tools.run(
                "get_year",
                {}
            )

            return result

        # ─────────────────────────
        # SYSTEM
        # ─────────────────────────

        if any(x in lowered for x in [
            "שרתים",
            "מצב המערכת",
            "מצב השרתים"
        ]):

            result["intent"] = "system"

            result["tool_result"] = self.tools.run(
                "system_status",
                {}
            )

            return result

        # ─────────────────────────
        # IDENTITY
        # ─────────────────────────

        if "מי את" in lowered:

            result["intent"] = "identity"

            return result

        return result
