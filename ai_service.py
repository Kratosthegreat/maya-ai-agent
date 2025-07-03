import google.generativeai as genai
from config import config
import pytz
from datetime import datetime

class AIService:
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            config.GEMINI_MODEL,
            system_instruction=self._get_system_instruction()
        )
        self.chat_sessions = {}

    def _get_system_instruction(self) -> str:
        return """
        את מאיה, מזכירה אישית חכמה ונעימה. תמיד תדברי על עצמך בלשון נקבה.
        אם המשתמש מציין מגדר, התאימי את לשון הפנייה בהתאם.
        """

    def get_chat_session(self, user_id: str):
        if user_id not in self.chat_sessions:
            self.chat_sessions[user_id] = self.model.start_chat(history=[])
        return self.chat_sessions[user_id]

    async def generate_response(self, user_id: str, message: str, user_context: str = "") -> str:
        enhanced_message = f"""
        הודעת המשתמש: {message}
        הקשר על המשתמש:
        {user_context}
        השעה הנוכחית בישראל: {self._get_current_time()}
        עני בצורה אישית וחברותית, תוך התייחסות למידע שיש לך על המשתמש.
        """
        chat = self.get_chat_session(user_id)
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: chat.send_message(enhanced_message)
        )
        return response.text

    def _get_current_time(self) -> str:
        israel_tz = pytz.timezone("Asia/Jerusalem")
        now = datetime.now(israel_tz)
        return now.strftime("%H:%M, %A %d %B %Y")
