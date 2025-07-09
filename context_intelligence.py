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
            relationship_stage=
