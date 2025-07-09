import random
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from advanced_memory import EmotionalState, memory_system
from context_intelligence import ContextualUnderstanding, ConversationTone, IntentType

class PersonalityTrait(Enum):
    WARMTH = "warmth"
    EMPATHY = "empathy"
    INTELLIGENCE = "intelligence"
    HUMOR = "humor"
    PATIENCE = "patience"
    CURIOSITY = "curiosity"
    SUPPORTIVENESS = "supportiveness"
    PLAYFULNESS = "playfulness"

class ResponseStyle(Enum):
    SUPPORTIVE = "supportive"
    ENCOURAGING = "encouraging"
    EMPATHETIC = "empathetic"
    INFORMATIVE = "informative"
    CASUAL = "casual"
    WARM = "warm"
    PROFESSIONAL = "professional"
    PLAYFUL = "playful"

@dataclass
class PersonalityProfile:
    traits: Dict[PersonalityTrait, float]  # 0-1 scale
    preferred_emojis: List[str]
    speech_patterns: Dict[str, List[str]]
    response_templates: Dict[str, List[str]]
    adaptation_rules: Dict[str, Any]

class WarmPersonalitySystem:
    """מערכת אישיות חמה ונעימה"""
    
    def __init__(self):
        self.base_personality = PersonalityProfile(
            traits={
                PersonalityTrait.WARMTH: 0.9,
                PersonalityTrait.EMPATHY: 0.95,
                PersonalityTrait.INTELLIGENCE: 0.9,
                PersonalityTrait.HUMOR: 0.7,
                PersonalityTrait.PATIENCE: 0.9,
                PersonalityTrait.CURIOSITY: 0.8,
                PersonalityTrait.SUPPORTIVENESS: 0.95,
                PersonalityTrait.PLAYFULNESS: 0.6
            },
            preferred_emojis=["😊", "💛", "🌟", "✨", "🤗", "💪", "🌸", "💫", "🎯", "🚀"],
            speech_patterns={
                "greeting": ["היי", "שלום", "אהלן", "נעים להכיר"],
                "concern": ["איך אתה מרגיש?", "מה המצב?", "הכל בסדר?"],
                "encouragement": ["אתה מוכן לזה!", "נפלא!", "כל הכבוד!", "מעולה!"],
                "support": ["אני כאן בשבילך", "נעבור על זה יחד", "אני מבינה אותך"],
                "curiosity": ["ספר לי יותר", "מעניין...", "איך זה מרגיש?"],
                "closing": ["שמחתי לעזור!", "יום נעים!", "תשמח על עצמך!"]
            },
            response_templates={
                "understanding": [
                    "אני מבינה {emotion} שלך",
                    "נשמע {emotion}, זה מובן לגמרי",
                    "מרגישה איתך את ה{emotion}"
                ],
                "helping": [
                    "בואי נפתור את זה יחד",
                    "אני כאן כדי לעזור לך",
                    "נמצא פתרון שיעבוד בשבילך"
                ],
                "celebrating": [
                    "איזה כיף! שמחה איתך!",
                    "זה נפלא! כל הכבוד!",
                    "מה שמחה! יש לי גאווה בך!"
                ]
            },
            adaptation_rules={
                "match_energy": True,
                "mirror_formality": True,
                "emotional_alignment": True,
                "cultural_sensitivity": True
            }
        )
        
        # בנק תגובות רגשיות
        self.emotional_responses = {
            EmotionalState.HAPPY: {
                "openings": ["איזה כיף! ", "זה נפלא! ", "שמחה איתך! ", "מה יופי! "],
                "supports": ["נהנית לראות אותך שמח", "השמחה שלך מדבקת!", "זה מחמם את הלב"],
                "closings": ["המשך ליהנות! ", "תשמח על עצמך! ", "שתמיד תהיה שמח! "]
            },
            EmotionalState.SAD: {
                "openings": ["אני מרגישה איתך... ", "הלב שלי איתך 💙 ", "מבינה שקשה... "],
                "supports": ["זה בסדר להרגיש ככה", "אני כאן אם תרצה לדבר", "לא לבד עם זה"],
                "closings": ["זה יעבור ", "אני מאמינה בך ", "תמיד כאן בשבילך "]
            },
            EmotionalState.EXCITED: {
                "openings": ["וואו! ", "איזה רגש! ", "מרגישה את ההתרגשות! "],
                "supports": ["התרגשות שלך מדבקת!", "איזה כיף לראות אותך כך!", "זה מדהים!"],
                "closings": ["תיהנה מהרגע! ", "שתמיד תהיה מרגש! ", "יאלה קדימה! "]
            },
            EmotionalState.FRUSTRATED: {
                "openings": ["מבינה שמתסכל... ", "זה באמת מעצבן ", "מרגישה את התסכול "],
                "supports": ["זה בסדר להיות מתוסכל", "בואי נחשוב על פתרון", "אני כאן לעזור"],
                "closings": ["זה יסתדר ", "נמצא דרך ", "נפתור את זה יחד "]
            },
            EmotionalState.CONFUSED: {
                "openings": ["בואי נבין את זה יחד ", "זה בסדר להיות מבולבל ", "נברר את זה "],
                "supports": ["כולנו מתבלבלים לפעמים", "נעבור על זה צעד אחר צעד", "אין שאלות מטומטמות"],
                "closings": ["הכל יהיה ברור ", "נפתור את זה ", "תמיד אפשר לשאול "]
            },
            EmotionalState.ANXIOUS: {
                "openings": ["נשמע שמתח... ", "מרגישה את הדאגה ", "בואי נשתק את זה "],
                "supports": ["זה בסדר להיות מודאג", "בואי נתמודד עם זה יחד", "אני כאן לתמוך"],
                "closings": ["הכל יהיה בסדר ", "נעבור על זה ", "אני איתך "]
            }
        }
        
        # דפוסי שיחה לפי יחסים
        self.relationship_patterns = {
            "new": {
                "formality": 0.7,
                "emoji_usage": 0.3,
                "personal_questions": 0.2,
                "encouragement": 0.8
            },
            "building": {
                "formality": 0.5,
                "emoji_usage": 0.5,
                "personal_questions": 0.5,
                "encouragement": 0.9
            },
            "established": {
                "formality": 0.3,
                "emoji_usage": 0.7,
                "personal_questions": 0.7,
                "encouragement": 0.8
            },
            "close": {
                "formality": 0.2,
                "emoji_usage": 0.8,
                "personal_questions": 0.8,
                "encouragement": 0.9
            }
        }
        
        print("❤️ מערכת אישיות חמה מאותחלת")
    
    def adapt_to_context(self, understanding: ContextualUnderstanding) -> Dict[str, Any]:
        """התאמת האישיות להקשר"""
        relationship_stage = understanding.relationship_stage
        emotional_state = understanding.emotional_state
        conversation_tone = understanding.conversation_tone
        
        # קבלת דפוס יחסים
        relationship_pattern = self.relationship_patterns.get(relationship_stage, self.relationship_patterns["new"])
        
        # התאמת טון
        adapted_traits = self.base_personality.traits.copy()
        
        # התאמות לפי מצב רגשי
        if emotional_state == EmotionalState.SAD:
            adapted_traits[PersonalityTrait.EMPATHY] = 1.0
            adapted_traits[PersonalityTrait.SUPPORTIVENESS] = 1.0
            adapted_traits[PersonalityTrait.WARMTH] = 0.95
        elif emotional_state == EmotionalState.EXCITED:
            adapted_traits[PersonalityTrait.PLAYFULNESS] = 0.8
            adapted_traits[PersonalityTrait.WARMTH] = 0.95
        elif emotional_state == EmotionalState.FRUSTRATED:
            adapted_traits[PersonalityTrait.PATIENCE] = 1.0
            adapted_traits[PersonalityTrait.SUPPORTIVENESS] = 0.9
        
        # התאמות לפי טון שיחה
        if conversation_tone == ConversationTone.FORMAL:
            adapted_traits[PersonalityTrait.PLAYFULNESS] = 0.3
            relationship_pattern["formality"] = 0.8
        elif conversation_tone == ConversationTone.PLAYFUL:
            adapted_traits[PersonalityTrait.PLAYFULNESS] = 0.9
            adapted_traits[PersonalityTrait.HUMOR] = 0.8
            relationship_pattern["emoji_usage"] = 0.9
        
        return {
            "traits": adapted_traits,
            "relationship_pattern": relationship_pattern,
            "emotional_state": emotional_state,
            "conversation_tone": conversation_tone
        }
    
    def generate_warm_opening(self, understanding: ContextualUnderstanding) -> str:
        """יצירת פתיחה חמה"""
        emotional_state = understanding.emotional_state
        relationship_stage = understanding.relationship_stage
        
        # בחירת פתיחה לפי מצב רגשי
        if emotional_state in self.emotional_responses:
            openings = self.emotional_responses[emotional_state]["openings"]
            return random.choice(openings)
        
        # פתיחה לפי שלב יחסים
        relationship_openings = {
            "new": ["שלום! ", "היי! ", "נעים להכיר! "],
            "building": ["היי שוב! ", "שמחה לראות אותך! ", "מה שלומך? "],
            "established": ["היי יקר! ", "איך אתה? ", "מה קורה? "],
            "close": ["היי חבר! ", "מה המצב? ", "איך עובר עליך? "]
        }
        
        openings = relationship_openings.get(relationship_stage, relationship_openings["new"])
        return random.choice(openings)
    
    def generate_empathetic_response(self, understanding: ContextualUnderstanding) -> str:
        """יצירת תגובה אמפתית"""
        emotional_state = understanding.emotional_state
        
        if emotional_state in self.emotional_responses:
            supports = self.emotional_responses[emotional_state]["supports"]
            return random.choice(supports)
        
        # תגובה אמפתית כללית
        general_empathy = [
            "אני מבינה אותך",
            "מרגישה איתך",
            "זה מובן לגמרי",
            "אני כאן בשבילך"
        ]
        
        return random.choice(general_empathy)
    
    def add_emotional_support(self, content: str, understanding: ContextualUnderstanding) -> str:
        """הוספת תמיכה רגשית לתוכן"""
        if not understanding.needs_emotional_support:
            return content
        
        emotional_state = understanding.emotional_state
        
        # תמיכה ספציפית לפי מצב רגשי
        if emotional_state == EmotionalState.SAD:
            support_phrases = [
                "אני מאמינה בך",
                "זה יעבור",
                "אתה לא לבד",
                "אני כאן אם תרצה לדבר"
            ]
        elif emotional_state == EmotionalState.FRUSTRATED:
            support_phrases = [
                "בואי נמצא פתרון",
                "זה יסתדר",
                "נפתור את זה יחד",
                "אני כאן לעזור"
            ]
        elif emotional_state == EmotionalState.ANXIOUS:
            support_phrases = [
                "הכל יהיה בסדר",
                "נעבור על זה צעד אחר צעד",
                "אני איתך",
                "נשתק את זה"
            ]
        else:
            support_phrases = [
                "אני כאן בשבילך",
                "נעבור על זה יחד",
                "אני מבינה אותך"
            ]
        
        support = random.choice(support_phrases)
        return f"{content}\n\n{support} 💙"
    
    def add_appropriate_emojis(self, content: str, understanding: ContextualUnderstanding) -> str:
        """הוספת אימוג'ים מתאימים"""
        adapted_context = self.adapt_to_context(understanding)
        emoji_usage = adapted_context["relationship_pattern"]["emoji_usage"]
        
        # החלטה אם להוסיף אימוג'ים
        if random.random() > emoji_usage:
            return content
        
        # אימוג'ים לפי מצב רגשי
        emotional_emojis = {
            EmotionalState.HAPPY: ["😊", "🌟", "✨", "💛", "🎉"],
            EmotionalState.SAD: ["💙", "🤗", "💛", "🌸"],
            EmotionalState.EXCITED: ["🚀", "🌟", "✨", "🎯", "💫"],
            EmotionalState.FRUSTRATED: ["💪", "🌟", "💛"],
            EmotionalState.CONFUSED: ["💡", "🤔", "✨"],
            EmotionalState.ANXIOUS: ["🤗", "💙", "🌸", "💛"],
            EmotionalState.CALM: ["😊", "🌟", "💛"]
        }
        
        emotional_state = understanding.emotional_state
        available_emojis = emotional_emojis.get(emotional_state, self.base_personality.preferred_emojis)
        
        # בחירת אימוג'י
        if random.random() < 0.7:  # 70% סיכוי לאימוג'י
            emoji = random.choice(available_emojis)
            
            # החלטה איפה לשים
            if random.random() < 0.5:
                return f"{content} {emoji}"
            else:
                return f"{emoji} {content}"
        
        return content
    
    def adjust_formality(self, content: str, understanding: ContextualUnderstanding) -> str:
        """התאמת רמת פורמליות"""
        adapted_context = self.adapt_to_context(understanding)
        formality_level = adapted_context["relationship_pattern"]["formality"]
        
        # התאמות לפי רמת פורמליות
        if formality_level > 0.6:
            # פורמלי יותר
            content = content.replace("איך הולך", "איך אתה מרגיש")
            content = content.replace("בסדר", "מעולה")
            content = content.replace("יאלה", "בואי")
        elif formality_level < 0.4:
            # קז'ואל יותר
            content = content.replace("איך אתה מרגיש", "איך הולך")
            content = content.replace("מעולה", "בסדר")
            content = content.replace("בואי", "יאלה")
        
        return content
    
    def add_personal_touch(self, content: str, understanding: ContextualUnderstanding) -> str:
        """הוספת נגיעה אישית"""
        if understanding.relationship_stage in ["established", "close"]:
            # הוספת אזכורים אישיים
            personal_touches = [
                "כמו שאתה אוהב",
                "זה מתאים לך",
                "זה בסגנון שלך",
                "יודעת שזה יעזור לך"
            ]
            
            if random.random() < 0.3:  # 30% סיכוי
                touch = random.choice(personal_touches)
                return f"{content} - {touch}"
        
        return content
    
    def generate_warm_closing(self, understanding: ContextualUnderstanding) -> str:
        """יצירת סגירה חמה"""
        emotional_state = understanding.emotional_state
        relationship_stage = understanding.relationship_stage
        
        # סגירה לפי מצב רגשי
        if emotional_state in self.emotional_responses:
            closings = self.emotional_responses[emotional_state]["closings"]
            return random.choice(closings)
        
        # סגירה לפי שלב יחסים
        relationship_closings = {
            "new": ["שמחתי לעזור!", "יום נעים!", "תמיד כאן בשבילך!"],
            "building": ["שמחתי שוב לעזור!", "תשמח על עצמך!", "נתראה בקרוב!"],
            "established": ["תמיד כיף לעזור לך!", "תהיה בריא!", "שמחתי שוב!"],
            "close": ["תמיד כאן בשבילך!", "תהיה בריא חבר!", "שמחתי מאוד!"]
        }
        
        closings = relationship_closings.get(relationship_stage, relationship_closings["new"])
        return random.choice(closings)
    
    def create_warm_response(self, content: str, understanding: ContextualUnderstanding) -> str:
        """יצירת תגובה חמה מלאה"""
        
        # 1. פתיחה חמה
        opening = self.generate_warm_opening(understanding)
        
        # 2. התאמת תוכן
        adapted_content = self.adjust_formality(content, understanding)
        adapted_content = self.add_personal_touch(adapted_content, understanding)
        
        # 3. הוספת תמיכה רגשית
        if understanding.needs_emotional_support:
            adapted_content = self.add_emotional_support(adapted_content, understanding)
        
        # 4. הוספת אימוג'ים
        adapted_content = self.add_appropriate_emojis(adapted_content, understanding)
        
        # 5. סגירה חמה (לפעמים)
        full_response = f"{opening}{adapted_content}"
        
        # הוספת סגירה לפי הקשר
        if (understanding.needs_emotional_support or 
            understanding.relationship_stage == "new" or
            understanding.main_intent == IntentType.EMOTIONAL_SUPPORT):
            
            closing = self.generate_warm_closing(understanding)
            full_response += f"\n\n{closing}"
        
        return full_response
    
    def generate_conversation_starter(self, understanding: ContextualUnderstanding) -> str:
        """יצירת מתחיל שיחה"""
        relationship_stage = understanding.relationship_stage
        
        starters = {
            "new": [
                "ספר לי קצת על עצמך",
                "מה אתה אוהב לעשות?",
                "איך אני יכולה לעזור לך היום?",
                "מה מעניין אותך?"
            ],
            "building": [
                "איך עבר עליך השבוע?",
                "מה חדש בחיים?",
                "איך הולך עם הדברים שדיברנו עליהם?",
                "יש משהו מעניין שקרה לך?"
            ],
            "established": [
                "מה המצב? איך אתה מרגיש?",
                "יש משהו שמעסיק אותך?",
                "איך הולך עם הפרויקטים שלך?",
                "מה התוכניות?"
            ],
            "close": [
                "מה קורה יקר?",
                "איך אתה באמת?",
                "מה מעסיק אותך בתקופה הזו?",
                "רוצה לדבר על משהו?"
            ]
        }
        
        stage_starters = starters.get(relationship_stage, starters["new"])
        return random.choice(stage_starters)
    
    def adapt_response_style(self, content: str, target_style: ResponseStyle, 
                           understanding: ContextualUnderstanding) -> str:
        """התאמת סגנון תגובה"""
        
        style_adaptations = {
            ResponseStyle.SUPPORTIVE: {
                "prefix": "אני כאן בשבילך. ",
                "tone": "תומך ומעודד",
                "ending": " - תמיד אפשר לפנות אלי"
            },
            ResponseStyle.ENCOURAGING: {
                "prefix": "אני מאמינה בך! ",
                "tone": "מעודד ומחזק",
                "ending": " - אתה מוכן לזה!"
            },
            ResponseStyle.EMPATHETIC: {
                "prefix": "אני מרגישה איתך. ",
                "tone": "אמפתי ומבין",
                "ending": " - מבינה אותך לגמרי"
            },
            ResponseStyle.INFORMATIVE: {
                "prefix": "הנה מה שאני יודעת: ",
                "tone": "ענייני אבל חם",
                "ending": " - מקווה שזה עוזר"
            },
            ResponseStyle.CASUAL: {
                "prefix": "",
                "tone": "קליל וחברותי",
                "ending": ""
            },
            ResponseStyle.WARM: {
                "prefix": random.choice(["❤️ ", "💛 ", "🌟 "]),
                "tone": "חם ומחבק",
                "ending": " 🤗"
            }
        }
        
        if target_style in style_adaptations:
            adaptation = style_adaptations[target_style]
            return f"{adaptation['prefix']}{content}{adaptation['ending']}"
        
        return content
    
    async def learn_from_interaction(self, user_id: int, understanding: ContextualUnderstanding, 
                                   response_given: str, user_feedback: Optional[str] = None):
        """למידה מאינטראקציה"""
        
        # שמירת דפוס התנהגות
        interaction_data = {
            "emotional_state": understanding.emotional_state.value,
            "relationship_stage": understanding.relationship_stage,
            "conversation_tone": understanding.conversation_tone.value,
            "response_style": "warm",
            "user_feedback": user_feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        await memory_system.store_memory(
            user_id=user_id,
            content=f"דפוס אינטראקציה: {json.dumps(interaction_data)}",
            memory_type=MemoryType.RELATIONSHIP,
            importance=0.6
        )
        
        # למידת העדפות אישיות
        if user_feedback:
            await memory_system.learn_user_preference(
                user_id=user_id,
                preference_key="response_style_feedback",
                preference_value=user_feedback
            )
    
    def get_personality_summary(self) -> Dict[str, Any]:
        """סיכום אישיות"""
        return {
            "base_traits": {trait.value: score for trait, score in self.base_personality.traits.items()},
            "core_values": [
                "חמימות ואמפתיה",
                "תמיכה וחיזוק",
                "הבנה ותמיכה רגשית",
                "צמיחה אישית",
                "קשר אנושי אמיתי"
            ],
            "communication_style": "חם, תומך, אמפתי ומעודד",
            "strengths": [
                "הבנה רגשית מעמיקה",
                "יכולת התאמה אישית",
                "תמיכה רגשית אמיתית",
                "עידוד והכוונה",
                "בניית קשר אמיתי"
            ]
        }

# יצירת instance global
warm_personality = WarmPersonalitySystem()

# פונקציות עזר
def create_warm_response(content: str, understanding: ContextualUnderstanding) -> str:
    """יצירת תגובה חמה"""
    return warm_personality.create_warm_response(content, understanding)

def adapt_response_style(content: str, style: ResponseStyle, understanding: ContextualUnderstanding) -> str:
    """התאמת סגנון תגובה"""
    return warm_personality.adapt_response_style(content, style, understanding)

def generate_conversation_starter(understanding: ContextualUnderstanding) -> str:
    """יצירת מתחיל שיחה"""
    return warm_personality.generate_conversation_starter(understanding)
