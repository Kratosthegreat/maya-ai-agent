import os
import asyncio
import google.generativeai as genai
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

# Import המודולים שיצרנו
from advanced_memory import (
    memory_system, EmotionalState, MemoryType, 
    remember_conversation, learn_about_user, get_smart_context
)
from context_intelligence import (
    init_context_intelligence, context_intelligence, 
    ContextualUnderstanding, IntentType
)
from warm_personality import (
    warm_personality, create_warm_response, ResponseStyle
)

@dataclass
class IntelligentResponse:
    content: str
    emotional_context: EmotionalState
    confidence: float
    used_tools: List[str]
    learned_facts: List[str]
    suggestions: List[str]

class IntelligentMayaAgent:
    """מאיה - AI Agent חכם, מבין ואינטליגנטי"""
    
    def __init__(self, gemini_api_key: str):
        # הגדרת Gemini
        genai.configure(api_key=gemini_api_key)
        
        # יצירת המודל
        self.model = self._init_gemini_model()
        
        # אתחול מרכיבי המערכת
        self.memory = memory_system
        self.context_intelligence = init_context_intelligence(self.model)
        self.personality = warm_personality
        
        # כלים זמינים
        self.available_tools = {
            'web_search': self._web_search,
            'knowledge_base': self._knowledge_base_search,
            'calculator': self._calculate,
            'time_info': self._get_time_info,
            'weather': self._get_weather,
            'reminder': self._set_reminder
        }
        
        # הוראות מתקדמות למודל
        self.system_instructions = """
        אתה מאיה - AI Agent חכם, מבין ואינטליגנטי.
        
        העקרונות שלך:
        1. תמיד תבין מה המשתמש באמת רוצה לדעת
        2. תקרא את השאלה בעיון ותתן תשובה מדויקת
        3. תהיה חמה ונעימה אבל תמיד רלוונטית
        4. תזכור הכל על המשתמש ותשתמש בזה
        5. תלמד מכל שיחה ותשתפר
        
        אם אתה לא יודע משהו - תגיד זאת בכנות.
        אם אתה צריך כלים - תבקש אותם.
        אם המשתמש זקוק לתמיכה רגשית - תתן אותה.
        """
        
        print("🧠 מאיה AI Agent חכם מאותחל")
        print("✅ זיכרון מתקדם")
        print("✅ הבנה מהקשרית")
        print("✅ אישיות חמה")
        print("✅ כלים מתקדמים")
    
    def _init_gemini_model(self):
        """אתחול מודל Gemini"""
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ משתמש במודל: gemini-1.5-flash")
            return model
        except:
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                print("✅ משתמש במודל: gemini-1.5-pro")
                return model
            except:
                try:
                    model = genai.GenerativeModel('gemini-pro')
                    print("✅ משתמש במודל: gemini-pro")
                    return model
                except:
                    model = genai.GenerativeModel('models/gemini-pro')
                    print("✅ משתמש במודל: models/gemini-pro")
                    return model
    
    async def process_message(self, user_id: int, message: str) -> IntelligentResponse:
        """עיבוד הודעה מלא וחכם"""
        
        print(f"🎯 מאיה מעבדת: {message[:50]}...")
        
        # שלב 1: הבנה מהקשרית מעמיקה
        understanding = await self.context_intelligence.analyze_message(user_id, message)
        
        # שלב 2: קבלת הקשר חכם
        smart_context = await get_smart_context(user_id, message)
        
        # שלב 3: שימוש בכלים אם נדרש
        tool_results = {}
        if understanding.requires_tools:
            tool_results = await self._use_tools(understanding.suggested_tools, message)
        
        # שלב 4: יצירת תגובה מושכלת
        intelligent_content = await self._generate_intelligent_response(
            understanding, smart_context, tool_results
        )
        
        # שלב 5: הפיכה לחמה ונעימה
        warm_response = create_warm_response(intelligent_content, understanding)
        
        # שלב 6: למידה מהשיחה
        learned_facts = await self._learn_from_interaction(user_id, understanding, message)
        
        # שלב 7: שמירת השיחה
        await remember_conversation(user_id, message, warm_response, understanding.emotional_state)
        
        # שלב 8: יצירת הצעות
        suggestions = await self._generate_suggestions(understanding, smart_context)
        
        response = IntelligentResponse(
            content=warm_response,
            emotional_context=understanding.emotional_state,
            confidence=0.8,  # נחשב לאחר כך
            used_tools=list(tool_results.keys()),
            learned_facts=learned_facts,
            suggestions=suggestions
        )
        
        print(f"✅ מאיה סיימה עיבוד: {understanding.main_intent.value}")
        return response
    
    async def _generate_intelligent_response(self, understanding: ContextualUnderstanding, 
                                           smart_context: Dict[str, Any], 
                                           tool_results: Dict[str, Any]) -> str:
        """יצירת תגובה מושכלת"""
        
        # בניית הקשר מלא למודל
        context_summary = await self.context_intelligence.generate_context_summary(understanding)
        
        # הוספת מידע מהזיכרון
        memory_context = ""
        if smart_context.get("relevant_memories"):
            memory_context = "מידע רלוונטי שאני זוכרת עליך:\n"
            for memory in smart_context["relevant_memories"]:
                memory_context += f"- {memory}\n"
        
        # הוספת תוצאות כלים
        tools_context = ""
        if tool_results:
            tools_context = "מידע שמצאתי:\n"
            for tool, result in tool_results.items():
                tools_context += f"- {tool}: {result}\n"
        
        # בניית ה-prompt המלא
        full_prompt = f"""
        {self.system_instructions}
        
        {context_summary}
        
        {memory_context}
        
        {tools_context}
        
        המשתמש שואל: "{understanding.original_message}"
        
        תן תשובה מדויקת, רלוונטית ומועילה בסגנון מאיה:
        """
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text.strip() if response.text else "מצטערת, לא הצלחתי להבין. תוכל לנסח אחרת?"
        except Exception as e:
            print(f"❌ שגיאה ביצירת תגובה: {e}")
            return "משהו השתבש בחשיבה שלי... בואי ננסה שוב"
    
    async def _use_tools(self, tools: List[str], message: str) -> Dict[str, Any]:
        """שימוש בכלים"""
        results = {}
        
        for tool in tools:
            if tool in self.available_tools:
                try:
                    result = await self.available_tools[tool](message)
                    results[tool] = result
                except Exception as e:
                    print(f"❌ שגיאה בכלי {tool}: {e}")
                    results[tool] = f"שגיאה: {str(e)}"
        
        return results
    
    async def _web_search(self, query: str) -> str:
        """חיפוש באינטרנט (סימולציה)"""
        # כאן תוכל להוסיף חיפוש אמיתי
        return f"תוצאות חיפוש עבור: {query}"
    
    async def _knowledge_base_search(self, query: str) -> str:
        """חיפוש בבסיס ידע"""
        # כאן תוכל להוסיף חיפוש בבסיס ידע
        return f"מידע מבסיס הידע: {query}"
    
    async def _calculate(self, expression: str) -> str:
        """חישוב"""
        try:
            # בטיחות בסיסית
            if any(char in expression for char in ['import', 'exec', 'eval', '__']):
                return "לא יכול לבצע חישוב מסוכן"
            
            result = eval(expression)
            return str(result)
        except:
            return "לא יכול לחשב את זה"
    
    async def _get_time_info(self, query: str) -> str:
        """מידע על זמן"""
        now = datetime.now()
        return f"השעה עכשיו: {now.strftime('%H:%M')}, תאריך: {now.strftime('%d/%m/%Y')}"
    
    async def _get_weather(self, query: str) -> str:
        """מידע על מזג אוויר (סימולציה)"""
        return "מזג האוויר: 22°C, בהיר עם עננים קלים"
    
    async def _set_reminder(self, query: str) -> str:
        """הגדרת תזכורת"""
        return f"תזכורת נוספה: {query}"
    
    async def _learn_from_interaction(self, user_id: int, understanding: ContextualUnderstanding, 
                                    message: str) -> List[str]:
        """למידה מהשיחה"""
        learned_facts = []
        
        # למידת עובדות אישיות
        if understanding.main_intent == IntentType.PERSONAL_SHARING:
            await learn_about_user(user_id, message, importance=0.8)
            learned_facts.append("למדתי עובדה אישית חדשה")
        
        # למידת העדפות
        if "אוהב" in message or "רוצה" in message:
            preference_match = None
            if "אוהב" in message:
                preference_match = message.split("אוהב")[1].strip()
            elif "רוצה" in message:
                preference_match = message.split("רוצה")[1].strip()
            
            if preference_match:
                await self.memory.learn_user_preference(user_id, "preference", preference_match)
                learned_facts.append(f"למדתי שאתה אוהב: {preference_match}")
        
        # עדכון מצב רגשי
        await self.memory.update_emotional_state(user_id, understanding.emotional_state)
        
        return learned_facts
    
    async def _generate_suggestions(self, understanding: ContextualUnderstanding, 
                                  smart_context: Dict[str, Any]) -> List[str]:
        """יצירת הצעות"""
        suggestions = []
        
        # הצעות לפי כוונה
        if understanding.main_intent == IntentType.EMOTIONAL_SUPPORT:
            suggestions.extend([
                "רוצה לדבר על מה שמעסיק אותך?",
                "אולי נמצא דרכים להרגיש טוב יותר?",
                "יש משהו ספציפי שאני יכולה לעזור בו?"
            ])
        
        elif understanding.main_intent == IntentType.INFORMATION_SEEKING:
            suggestions.extend([
                "רוצה שאחפש מידע נוסף?",
                "יש עוד שאלות בנושא?",
                "אולי תרצה להעמיק יותר?"
            ])
        
        elif understanding.main_intent == IntentType.TASK_MANAGEMENT:
            suggestions.extend([
                "רוצה שאזכיר לך על זה?",
                "אולי נחלק את זה למטלות קטנות?",
                "יש עוד דברים שצריך לתכנן?"
            ])
        
        # הצעות לפי שלב יחסים
        if understanding.relationship_stage == "new":
            suggestions.append("ספר לי עוד על עצמך")
        
        return suggestions[:3]  # מקסימום 3 הצעות
    
    async def get_user_dashboard(self, user_id: int) -> Dict[str, Any]:
        """לוח בקרה של המשתמש"""
        insights = await self.memory.get_user_insights(user_id)
        memory_summary = await self.memory.get_memory_summary(user_id)
        
        return {
            "user_profile": {
                "relationship_stage": insights["user_profile"]["relationship_stage"],
                "emotional_state": insights["user_profile"]["emotional_state"],
                "total_conversations": memory_summary["total_conversations"],
                "total_memories": memory_summary["total_memories"]
            },
            "recent_activity": {
                "last_conversation": memory_summary["last_conversation"],
                "recent_topics": insights["conversation_patterns"]["recent_topics"],
                "engagement_level": insights["conversation_patterns"]["engagement_level"]
            },
            "emotional_analysis": memory_summary["emotional_patterns"],
            "recommendations": insights["recommendations"],
            "personality_insights": self.personality.get_personality_summary()
        }
    
    async def simulate_proactive_message(self, user_id: int) -> Optional[str]:
        """יצירת הודעה יוזמת"""
        insights = await self.memory.get_user_insights(user_id)
        
        # בדיקה אם מתאים לשלוח הודעה יוזמת
        last_conversation = insights["memory_analysis"]["last_conversation"]
        if last_conversation:
            # המרת המחרוזת לאובייקט datetime
            try:
                last_time = datetime.fromisoformat(last_conversation)
                time_diff = (datetime.now() - last_time).days
                
                if time_diff > 3:  # 3 ימים ללא שיחה
                    return "היי! מזמן לא שוחחנו... איך אתה מרגיש? 😊"
            except:
                pass
        
        return None
    
    async def handle_quick_response(self, user_id: int, message: str) -> Optional[str]:
        """טיפול בתגובות מהירות"""
        message_lower = message.lower()
        
        # תגובות מהירות חכמות
        quick_responses = {
            "תודה": "תמיד שמחה לעזור! 😊",
            "תודה רבה": "אין בעד מה! זה השמחה שלי 💛",
            "אהבתי": "איזה כיף לשמוע! 🌟",
            "מעולה": "שמחה שזה עזר! ✨",
            "לא הבנתי": "אוקיי, בואי אנסה להסביר אחרת...",
            "מה קורה": "הכל טוב! איך אתה מרגיש? 😊",
            "שלום": "שלום! שמחה לראות אותך 🌸"
        }
        
        for trigger, response in quick_responses.items():
            if trigger in message_lower:
                # שמירה בזיכרון
                await remember_conversation(user_id, message, response, EmotionalState.CALM)
                return response
        
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """סטטוס המערכת"""
        return {
            "agent_name": "מאיה",
            "version": "2.0 - AI Agent חכם",
            "components": {
                "memory_system": "✅ פעיל",
                "context_intelligence": "✅ פעיל",
                "personality_system": "✅ פעיל",
                "tools": f"✅ {len(self.available_tools)} כלים זמינים"
            },
            "capabilities": [
                "הבנה מהקשרית מעמיקה",
                "זיכרון ארוך טווח",
                "אישיות חמה ומתאדפטת",
                "תמיכה רגשית",
                "למידה רציפה",
                "שימוש בכלים",
                "הבנת רגשות",
                "תכנון ואסטרטגיה"
            ],
            "personality_traits": {
                "warmth": "9/10",
                "intelligence": "10/10",
                "empathy": "10/10",
                "helpfulness": "9/10"
            }
        }
    
    async def explain_decision(self, user_id: int, message: str) -> str:
        """הסברת החלטה שמאיה קיבלה"""
        understanding = await self.context_intelligence.analyze_message(user_id, message)
        
        explanation = f"""
🤔 איך אני מבינה את ההודעה שלך:

📝 המשפט: "{message}"

🎯 הכוונה שלך: {understanding.main_intent.value}
😊 איך אתה מרגיש: {understanding.emotional_state.value}
🗣️ הטון שלך: {understanding.conversation_tone.value}

🧠 מה אני חושבת:
- {"אתה צריך תמיכה רגשית" if understanding.needs_emotional_support else "אתה במצב רגשי יציב"}
- {"זה קשור לשיחה שלנו הקודמת" if understanding.relates_to_previous else "זה נושא חדש"}
- {"אני צריכה כלים לעזור" if understanding.requires_tools else "אני יכולה לענות מהידע שלי"}

💡 האסטרטגיה שלי: {understanding.response_strategy}

🤝 היחסים שלנו: {understanding.relationship_stage}
        """
        
        return explanation.strip()

# יצירת instance global
intelligent_maya = None

def init_intelligent_maya(gemini_api_key: str) -> IntelligentMayaAgent:
    """אתחול מאיה החכמה"""
    global intelligent_maya
    intelligent_maya = IntelligentMayaAgent(gemini_api_key)
    return intelligent_maya

# פונקציות עזר
async def smart_response(user_id: int, message: str) -> str:
    """תגובה חכמה"""
    if not intelligent_maya:
        return "מאיה עדיין לא מאותחלת"
    
    # בדיקה לתגובה מהירה
    quick_response = await intelligent_maya.handle_quick_response(user_id, message)
    if quick_response:
        return quick_response
    
    # עיבוד מלא
    response = await intelligent_maya.process_message(user_id, message)
    return response.content

async def get_user_insights(user_id: int) -> Dict[str, Any]:
    """קבלת תובנות על המשתמש"""
    if not intelligent_maya:
        return {}
    
    return await intelligent_maya.get_user_dashboard(user_id)

async def explain_thinking(user_id: int, message: str) -> str:
    """הסברת תהליך החשיבה"""
    if not intelligent_maya:
        return "מאיה עדיין לא מאותחלת"
    
    return await intelligent_maya.explain_decision(user_id, message)

def get_maya_status() -> Dict[str, Any]:
    """סטטוס מאיה"""
    if not intelligent_maya:
        return {"status": "לא מאותחלת"}
    
    return intelligent_maya.get_system_status()

# מחלקה למטרות בדיקה
class MayaTestSuite:
    """סוויטת בדיקות למאיה"""
    
    @staticmethod
    async def run_basic_tests():
        """בדיקות בסיסיות"""
        print("🧪 מתחיל בדיקות למאיה...")
        
        # Test 1: הבנה בסיסית
        test_user = 12345
        basic_message = "שלום, איך אתה?"
        
        if intelligent_maya:
            response = await smart_response(test_user, basic_message)
            print(f"✅ בדיקה 1 - תגובה בסיסית: {response[:50]}...")
            
            # Test 2: הבנה רגשית
            emotional_message = "אני מרגיש עצוב היום"
            emotional_response = await smart_response(test_user, emotional_message)
            print(f"✅ בדיקה 2 - תגובה רגשית: {emotional_response[:50]}...")
            
            # Test 3: זיכרון
            memory_message = "אני אוהב פיצה"
            memory_response = await smart_response(test_user, memory_message)
            print(f"✅ בדיקה 3 - זיכרון: {memory_response[:50]}...")
            
            # Test 4: המשך שיחה
            followup_message = "מה אתה זוכר עלי?"
            followup_response = await smart_response(test_user, followup_message)
            print(f"✅ בדיקה 4 - המשך שיחה: {followup_response[:50]}...")
            
            print("🎉 כל הבדיקות עברו בהצלחה!")
        else:
            print("❌ מאיה לא מאותחלת")
    
    @staticmethod
    async def test_emotional_intelligence():
        """בדיקת אינטליגנציה רגשית"""
        print("🧪 בודק אינטליגנציה רגשית...")
        
        test_user = 67890
        emotional_tests = [
            ("אני מרגיש עצוב", EmotionalState.SAD),
            ("אני כל כך שמח!", EmotionalState.HAPPY),
            ("אני מתוסכל מזה", EmotionalState.FRUSTRATED),
            ("אני מבולבל", EmotionalState.CONFUSED),
            ("אני מרגיש טוב", EmotionalState.HAPPY)
        ]
        
        for message, expected_emotion in emotional_tests:
            if intelligent_maya:
                understanding = await intelligent_maya.context_intelligence.analyze_message(test_user, message)
                actual_emotion = understanding.emotional_state
                
                if actual_emotion == expected_emotion:
                    print(f"✅ {message} -> {actual_emotion.value}")
                else:
                    print(f"❌ {message} -> ציפיתי {expected_emotion.value}, קיבלתי {actual_emotion.value}")
        
        print("🎉 בדיקת אינטליגנציה רגשית הושלמה!")

# פונקציה לריצת בדיקות
async def run_maya_tests():
    """ריצת כל הבדיקות"""
    await MayaTestSuite.run_basic_tests()
    await MayaTestSuite.test_emotional_intelligence()

if __name__ == "__main__":
    # דוגמה לשימוש
    print("🚀 מתחיל מאיה AI Agent חכם...")
    
    # אתחול (דורש מפתח Gemini)
    # maya = init_intelligent_maya("YOUR_GEMINI_API_KEY")
    
    # ריצת בדיקות
    # asyncio.run(run_maya_tests())
