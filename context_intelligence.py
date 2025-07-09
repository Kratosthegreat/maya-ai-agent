import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import google.generativeai as genai
from datetime import datetime
from advanced_memory import EmotionalState, MemoryType, memory_system

class IntentType(Enum):
    QUESTION = "question"
    REQUEST = "request"
    CONVERSATION = "conversation"
    EMOTIONAL_SUPPORT = "emotional_support"
    TASK_MANAGEMENT = "task_management"
    INFORMATION_SEEKING = "information_seeking"
    CREATIVE = "creative"
    PLANNING = "planning"
    LEARNING = "learning"
    PERSONAL_SHARING = "personal_sharing"

class UrgencyLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ConversationTone(Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    EMOTIONAL = "emotional"
    TECHNICAL = "technical"
    SUPPORTIVE = "supportive"
    PLAYFUL = "playful"

@dataclass
class ContextualUnderstanding:
    user_id: int
    original_message: str
    
    # הבנה בסיסית
    main_intent: IntentType
    sub_intents: List[IntentType]
    entities: Dict[str, Any]
    
    # הקשר רגשי
    emotional_state: EmotionalState
    emotional_intensity: float  # 0-1
    needs_emotional_support: bool
    
    # הקשר שיחה
    conversation_tone: ConversationTone
    formality_level: float  # 0-1
    urgency: UrgencyLevel
    
    # הקשר היסטורי
    relates_to_previous: bool
    previous_context: Optional[str]
    topic_continuity: bool
    
    # מטא-מידע
    complexity_level: float  # 0-1
    requires_tools: bool
    suggested_tools: List[str]
    
    # תובנות
    user_insights: Dict[str, Any]
    response_strategy: str
    
    # אמון ויחסים
    trust_level: float  # 0-1
    relationship_stage: str  # "new", "building", "established", "close"

class AdvancedContextIntelligence:
    """מנוע הבנה מהקשרית מתקדם"""
    
    def __init__(self, gemini_model):
        self.gemini = gemini_model
        self.memory = memory_system
        
        # דפוסי זיהוי
        self.emotional_patterns = {
            'sad': ['עצוב', 'לא טוב', 'קשה', 'דיכאון', 'רע', 'כואב'],
            'happy': ['שמח', 'מעולה', 'נהדר', 'טוב', 'נפלא', 'גדול'],
            'excited': ['נרגש', 'מתרגש', 'וואו', 'אמייזינג', 'מגניב'],
            'frustrated': ['מעצבן', 'לא הגיוני', 'מעפן', 'מתסכל', 'בלגן'],
            'confused': ['לא מבין', 'מבולבל', 'מה זה', 'איך', 'מה הכוונה'],
            'anxious': ['מדאיג', 'לחוץ', 'חרדה', 'פוחד', 'מתח']
        }
        
        self.intent_patterns = {
            'question': ['מה', 'איך', 'למה', 'מתי', 'איפה', 'מי', 'כמה', '?'],
            'request': ['תעשה', 'תכין', 'תעזור', 'תמצא', 'תכתוב', 'תשלח'],
            'emotional_support': ['קשה לי', 'עצוב', 'צריך תמיכה', 'לא בא לי'],
            'task_management': ['תזכיר', 'מטלה', 'משימה', 'תכנן', 'ארגן'],
            'personal_sharing': ['אני', 'שמי', 'אוהב', 'רוצה', 'חושב', 'מרגיש']
        }
        
        self.urgency_indicators = {
            'critical': ['דחוף', 'מיד', 'חירום', 'עכשיו', 'מהר'],
            'high': ['בהקדם', 'חשוב', 'מאוד', 'צריך מהר'],
            'medium': ['כשתוכל', 'בבקשה', 'אשמח'],
            'low': ['אם יש זמן', 'כשנוח', 'לא דחוף']
        }
        
        print("🧠 מנוע הבנה מהקשרית מאותחל")
    
    async def analyze_message(self, user_id: int, message: str) -> ContextualUnderstanding:
        """ניתוח מקיף של הודעה"""
        print(f"🔍 מנתח הודעה: {message[:50]}...")
        
        # קבלת הקשר קיים
        context = await self.memory.get_conversation_context(user_id)
        insights = await self.memory.get_user_insights(user_id)
        
        # ניתוח בסיסי
        main_intent = self.detect_main_intent(message)
        sub_intents = self.detect_sub_intents(message)
        entities = self.extract_entities(message)
        
        # ניתוח רגשי
        emotional_state = self.analyze_emotional_state(message)
        emotional_intensity = self.calculate_emotional_intensity(message)
        needs_support = self.assess_emotional_support_need(message, emotional_state)
        
        # ניתוח שיחה
        tone = self.detect_conversation_tone(message)
        formality = self.calculate_formality_level(message)
        urgency = self.detect_urgency_level(message)
        
        # ניתוח היסטורי
        relates_to_previous = self.check_previous_relation(message, context)
        previous_context = self.extract_previous_context(message, context)
        topic_continuity = self.assess_topic_continuity(message, context)
        
        # ניתוח מורכבות
        complexity = self.calculate_complexity_level(message)
        requires_tools = self.assess_tool_requirement(message, main_intent)
        suggested_tools = self.suggest_tools(message, main_intent)
        
        # אמון ויחסים
        trust_level = self.calculate_trust_level(insights)
        relationship_stage = self.assess_relationship_stage(insights)
        
        # אסטרטגיית תגובה
        response_strategy = await self.determine_response_strategy(
            main_intent, emotional_state, relationship_stage, context
        )
        
        understanding = ContextualUnderstanding(
            user_id=user_id,
            original_message=message,
            main_intent=main_intent,
            sub_intents=sub_intents,
            entities=entities,
            emotional_state=emotional_state,
            emotional_intensity=emotional_intensity,
            needs_emotional_support=needs_support,
            conversation_tone=tone,
            formality_level=formality,
            urgency=urgency,
            relates_to_previous=relates_to_previous,
            previous_context=previous_context,
            topic_continuity=topic_continuity,
            complexity_level=complexity,
            requires_tools=requires_tools,
            suggested_tools=suggested_tools,
            user_insights=insights,
            response_strategy=response_strategy,
            trust_level=trust_level,
            relationship_stage=relationship_stage
        )
        
        # שמירת הבנה בזיכרון
        await self.memory.store_memory(
            user_id=user_id,
            content=f"הבנה מהקשרית: {main_intent.value} - {emotional_state.value}",
            memory_type=MemoryType.CONTEXT,
            importance=0.7,
            emotional_context=emotional_state
        )
        
        print(f"✅ הבנה מושלמת: {main_intent.value} | {emotional_state.value} | {relationship_stage}")
        return understanding
    
    def detect_main_intent(self, message: str) -> IntentType:
        """זיהוי הכוונה העיקרית"""
        message_lower = message.lower()
        
        # בדיקת דפוסים לפי עדיפות
        if any(pattern in message_lower for pattern in self.intent_patterns['emotional_support']):
            return IntentType.EMOTIONAL_SUPPORT
        elif any(pattern in message_lower for pattern in self.intent_patterns['task_management']):
            return IntentType.TASK_MANAGEMENT
        elif any(pattern in message_lower for pattern in self.intent_patterns['question']):
            return IntentType.QUESTION
        elif any(pattern in message_lower for pattern in self.intent_patterns['request']):
            return IntentType.REQUEST
        elif any(pattern in message_lower for pattern in self.intent_patterns['personal_sharing']):
            return IntentType.PERSONAL_SHARING
        else:
            return IntentType.CONVERSATION
    
    def detect_sub_intents(self, message: str) -> List[IntentType]:
        """זיהוי כוונות משניות"""
        sub_intents = []
        message_lower = message.lower()
        
        for intent_type, patterns in self.intent_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                try:
                    sub_intent = IntentType(intent_type)
                    sub_intents.append(sub_intent)
                except ValueError:
                    continue
        
        return sub_intents
    
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """חילוץ ישויות מהטקסט"""
        entities = {}
        
        # זיהוי זמנים
        time_patterns = {
            'מחר': 'tomorrow',
            'היום': 'today',
            'מחרתיים': 'day_after_tomorrow',
            'השבוע': 'this_week',
            'החודש': 'this_month'
        }
        
        for hebrew_time, english_time in time_patterns.items():
            if hebrew_time in message:
                entities['time'] = english_time
        
        # זיהוי מספרים
        numbers = re.findall(r'\d+', message)
        if numbers:
            entities['numbers'] = [int(n) for n in numbers]
        
        # זיהוי אזכורים אישיים
        personal_indicators = ['אני', 'שמי', 'אוהב', 'רוצה', 'צריך']
        if any(indicator in message for indicator in personal_indicators):
            entities['personal_info'] = True
        
        return entities
    
    def analyze_emotional_state(self, message: str) -> EmotionalState:
        """ניתוח מצב רגשי"""
        message_lower = message.lower()
        
        # ניקוד רגשי
        emotional_scores = {}
        
        for emotion, patterns in self.emotional_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            if score > 0:
                emotional_scores[emotion] = score
        
        # בחירת הרגש הדומיננטי
        if not emotional_scores:
            return EmotionalState.CALM
        
        dominant_emotion = max(emotional_scores, key=emotional_scores.get)
        
        # מיפוי לEmotionalState
        emotion_mapping = {
            'sad': EmotionalState.SAD,
            'happy': EmotionalState.HAPPY,
            'excited': EmotionalState.EXCITED,
            'frustrated': EmotionalState.FRUSTRATED,
            'confused': EmotionalState.CONFUSED,
            'anxious': EmotionalState.ANXIOUS
        }
        
        return emotion_mapping.get(dominant_emotion, EmotionalState.CALM)
    
    def calculate_emotional_intensity(self, message: str) -> float:
        """חישוב עוצמה רגשית"""
        intensity_indicators = {
            'מאוד': 0.8,
            'בטירוף': 0.9,
            'נורא': 0.7,
            'קצת': 0.3,
            'מעט': 0.2,
            '!!!': 0.8,
            '!': 0.6,
            'נוראי': 0.8,
            'הרבה': 0.7
        }
        
        base_intensity = 0.5
        message_lower = message.lower()
        
        for indicator, intensity in intensity_indicators.items():
            if indicator in message_lower:
                base_intensity = max(base_intensity, intensity)
        
        # התאמה לפי אורך ההודעה
        if len(message) > 200:
            base_intensity += 0.1
        
        return min(base_intensity, 1.0)
    
    def assess_emotional_support_need(self, message: str, emotional_state: EmotionalState) -> bool:
        """הערכה אם נדרשת תמיכה רגשית"""
        support_indicators = [
            'קשה לי', 'עצוב', 'לא בא לי', 'מתסכל', 'לא יודע מה לעשות',
            'צריך עזרה', 'בבעיה', 'מבולבל', 'לחוץ', 'מדאיג'
        ]
        
        return (emotional_state in [EmotionalState.SAD, EmotionalState.ANXIOUS, EmotionalState.FRUSTRATED] or
                any(indicator in message.lower() for indicator in support_indicators))
    
    def detect_conversation_tone(self, message: str) -> ConversationTone:
        """זיהוי טון שיחה"""
        message_lower = message.lower()
        
        # אינדיקטורים לטונים שונים
        tone_indicators = {
            'casual': ['בסדר', 'אוקיי', 'יאלה', 'מה קורה', 'מה נשמע'],
            'formal': ['אבקש', 'בבקשה', 'תודה רבה', 'לכבודי'],
            'emotional': ['מרגיש', 'כואב', 'שמח', 'עצוב', 'נרגש'],
            'technical': ['איך עובד', 'מה ההבדל', 'הסבר לי', 'מה זה'],
            'supportive': ['תעזור', 'צריך עזרה', 'תמיכה', 'לא יודע'],
            'playful': ['חחחח', 'מגניב', 'כיף', 'יש!', 'וואו']
        }
        
        tone_scores = {}
        for tone, indicators in tone_indicators.items():
            score = sum(1 for indicator in indicators if indicator in message_lower)
            if score > 0:
                tone_scores[tone] = score
        
        if not tone_scores:
            return ConversationTone.CASUAL
        
        dominant_tone = max(tone_scores, key=tone_scores.get)
        return ConversationTone(dominant_tone)
    
    def calculate_formality_level(self, message: str) -> float:
        """חישוב רמת פורמליות"""
        formal_indicators = ['אבקש', 'בבקשה', 'תודה רבה', 'לכבודי', 'מכובד']
        casual_indicators = ['בסדר', 'אוקיי', 'יאלה', 'מה קורה', 'חלאס']
        
        message_lower = message.lower()
        
        formal_score = sum(1 for indicator in formal_indicators if indicator in message_lower)
        casual_score = sum(1 for indicator in casual_indicators if indicator in message_lower)
        
        if formal_score + casual_score == 0:
            return 0.5  # ניטרלי
        
        return formal_score / (formal_score + casual_score)
    
    def detect_urgency_level(self, message: str) -> UrgencyLevel:
        """זיהוי רמת דחיפות"""
        message_lower = message.lower()
        
        for level, indicators in self.urgency_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                return UrgencyLevel[level.upper()]
        
        return UrgencyLevel.MEDIUM
    
    def check_previous_relation(self, message: str, context) -> bool:
        """בדיקה אם ההודעה קשורה לקודמת"""
        reference_indicators = [
            'זה', 'זאת', 'הדבר הזה', 'מה שאמרת', 'כמו שאמרתי',
            'בהמשך', 'חזרה', 'שוב', 'עוד', 'גם'
        ]
        
        return any(indicator in message.lower() for indicator in reference_indicators)
    
    def extract_previous_context(self, message: str, context) -> Optional[str]:
        """חילוץ הקשר קודם"""
        if context.conversation_flow:
            recent_message = context.conversation_flow[0]
            if self.check_previous_relation(message, context):
                return recent_message
        return None
    
    def assess_topic_continuity(self, message: str, context) -> bool:
        """הערכת רציפות נושא"""
        if not context.current_topic:
            return False
        
        # בדיקה אם הנושא הנוכחי מוזכר בהודעה
        return context.current_topic.lower() in message.lower()
    
    def calculate_complexity_level(self, message: str) -> float:
        """חישוב רמת מורכבות"""
        complexity_indicators = {
            'multi_questions': len(re.findall(r'[?]', message)) > 1,
            'long_message': len(message) > 200,
            'multiple_topics': len(message.split('.')) > 3,
            'technical_terms': any(term in message.lower() for term in ['איך עובד', 'מה ההבדל', 'הסבר']),
            'emotional_complexity': any(term in message.lower() for term in ['מרגיש', 'חושב', 'מבולבל'])
        }
        
        complexity_score = sum(1 for indicator in complexity_indicators.values() if indicator)
        return min(complexity_score / len(complexity_indicators), 1.0)
    
    def assess_tool_requirement(self, message: str, intent: IntentType) -> bool:
        """הערכה אם נדרשים כלים"""
        tool_requiring_patterns = [
            'חפש', 'מצא', 'בדוק', 'מה מזג האוויר', 'מה השעה',
            'חשב', 'תכין רשימה', 'תשלח', 'תזכיר'
        ]
        
        return (any(pattern in message.lower() for pattern in tool_requiring_patterns) or
                intent in [IntentType.INFORMATION_SEEKING, IntentType.TASK_MANAGEMENT])
    
    def suggest_tools(self, message: str, intent: IntentType) -> List[str]:
        """הצעת כלים רלוונטיים"""
        tools = []
        message_lower = message.lower()
        
        tool_patterns = {
            'web_search': ['חפש', 'מצא', 'בדוק באינטרנט', 'מה חדש'],
            'calculator': ['חשב', 'כמה זה', 'מה זה פלוס', 'מינוס'],
            'weather': ['מזג אוויר', 'גשם', 'חם', 'קר'],
            'timer': ['תזכיר', 'בעוד', 'מחר', 'השבוע'],
            'knowledge_base': ['מה זה', 'הסבר', 'איך עובד', 'למה']
        }
        
        for tool, patterns in tool_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                tools.append(tool)
        
        return tools
    
    def calculate_trust_level(self, insights: Dict[str, Any]) -> float:
        """חישוב רמת אמון"""
        base_trust = 0.3
        
        # הגדלת אמון לפי אינטראקציות
        total_conversations = insights.get('memory_analysis', {}).get('total_conversations', 0)
        interaction_boost = min(total_conversations * 0.05, 0.4)
        
        # הגדלת אמון לפי שיתוף מידע אישי
        personal_memories = insights.get('memory_analysis', {}).get('memory_breakdown', {}).get('personal_fact', {}).get('count', 0)
        personal_boost = min(personal_memories * 0.1, 0.3)
        
        return min(base_trust + interaction_boost + personal_boost, 1.0)
    
    def assess_relationship_stage(self, insights: Dict[str, Any]) -> str:
        """הערכת שלב היחסים"""
        total_conversations = insights.get('memory_analysis', {}).get('total_conversations', 0)
        personal_memories = insights.get('memory_analysis', {}).get('memory_breakdown', {}).get('personal_fact', {}).get('count', 0)
        
        if total_conversations == 0:
            return "new"
        elif total_conversations < 5:
            return "building"
        elif total_conversations < 20 or personal_memories < 5:
            return "established"
        else:
            return "close"
    
    async def determine_response_strategy(self, intent: IntentType, emotional_state: EmotionalState, 
                                        relationship_stage: str, context) -> str:
        """קביעת אסטרטגיית תגובה"""
        strategies = {
            "emotional_support_new": "תמיכה עדינה ובניית אמון",
            "emotional_support_close": "תמיכה עמוקה ואמפתיה מלאה",
            "information_formal": "מידע מדויק ומובנה",
            "information_casual": "מידע בטון חברותי",
            "conversation_building": "שיחה מעמיקה ולמידה על המשתמש",
            "conversation_established": "שיחה טבעית עם הקשר אישי",
            "task_efficient": "ביצוע מהיר ויעיל",
            "task_supportive": "ביצוע עם הדרכה ותמיכה"
        }
        
        # בחירת אסטרטגיה
        if intent == IntentType.EMOTIONAL_SUPPORT:
            return strategies["emotional_support_close" if relationship_stage == "close" else "emotional_support_new"]
        elif intent == IntentType.INFORMATION_SEEKING:
            return strategies["information_casual" if relationship_stage in ["established", "close"] else "information_formal"]
        elif intent == IntentType.TASK_MANAGEMENT:
            return strategies["task_supportive" if relationship_stage == "new" else "task_efficient"]
        elif intent == IntentType.CONVERSATION:
            return strategies["conversation_established" if relationship_stage in ["established", "close"] else "conversation_building"]
        else:
            return "תגובה מותאמת אישית"
    
    async def generate_context_summary(self, understanding: ContextualUnderstanding) -> str:
        """יצירת סיכום הבנה להדרכת המודל"""
        summary = f"""
הבנה מהקשרית של ההודעה:

🎯 כוונה עיקרית: {understanding.main_intent.value}
😊 מצב רגשי: {understanding.emotional_state.value} (עוצמה: {understanding.emotional_intensity:.1f})
🗣️ טון שיחה: {understanding.conversation_tone.value}
⚡ דחיפות: {understanding.urgency.value}
🤝 שלב יחסים: {understanding.relationship_stage}

💡 אסטרטגיית תגובה: {understanding.response_strategy}

{"🆘 נדרשת תמיכה רגשית" if understanding.needs_emotional_support else ""}
{"🔧 נדרשים כלים: " + ", ".join(understanding.suggested_tools) if understanding.requires_tools else ""}
{"📚 קשור לשיחה קודמת: " + understanding.previous_context if understanding.relates_to_previous else ""}
        """
        
        return summary.strip()

# יצירת instance global
context_intelligence = None

def init_context_intelligence(gemini_model):
    """אתחול מנוע ההבנה המהקשרית"""
    global context_intelligence
    context_intelligence = AdvancedContextIntelligence(gemini_model)
    return context_intelligence
