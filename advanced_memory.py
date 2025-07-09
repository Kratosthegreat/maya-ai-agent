import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
from pydantic import BaseModel

class MemoryType(Enum):
    CONVERSATION = "conversation"
    PERSONAL_FACT = "personal_fact"
    PREFERENCE = "preference"
    EMOTIONAL_STATE = "emotional_state"
    GOAL = "goal"
    RELATIONSHIP = "relationship"
    SKILL = "skill"
    CONTEXT = "context"

class EmotionalState(Enum):
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    CALM = "calm"
    ANXIOUS = "anxious"

@dataclass
class Memory:
    id: str
    user_id: int
    content: str
    memory_type: MemoryType
    importance: float  # 0-1
    emotional_context: Optional[EmotionalState]
    created_at: datetime
    last_accessed: datetime
    access_count: int
    metadata: Dict[str, Any]

@dataclass
class ConversationContext:
    user_id: int
    current_topic: Optional[str]
    emotional_state: EmotionalState
    recent_memories: List[Memory]
    conversation_flow: List[str]
    user_preferences: Dict[str, Any]

class AdvancedMemorySystem:
    """מערכת זיכרון מתקדמת עם יכולות סמנטיות ורגשיות"""
    
    def __init__(self, db_path: str = "advanced_memory.db"):
        self.db_path = db_path
        self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Vector Database
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.vector_collection = self.chroma_client.get_or_create_collection(
            name="agent_memories",
            metadata={"hnsw:space": "cosine"}
        )
        
        # SQLite for structured data
        self.init_database()
        
        # Context cache
        self.context_cache: Dict[int, ConversationContext] = {}
        
        print("🧠 מערכת זיכרון מתקדמת מאותחלת")
        print(f"📊 Vector embeddings: {self.embeddings.get_sentence_embedding_dimension()} dimensions")
    
    def init_database(self):
        """יצירת מסד הנתונים המתקדם"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # טבלת זיכרונות
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                emotional_context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                metadata TEXT,
                embedding_id TEXT
            )
        """)
        
        # טבלת פרופילי משתמשים
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                personality_traits TEXT,
                preferences TEXT,
                emotional_patterns TEXT,
                relationship_context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # טבלת שיחות
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                emotional_context TEXT,
                topic TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # טבלת מטרות
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_description TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                progress REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                target_date TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """יצירת embedding לטקסט"""
        return self.embeddings.encode(text)
    
    async def store_memory(self, user_id: int, content: str, memory_type: MemoryType, 
                          importance: float = 0.5, emotional_context: Optional[EmotionalState] = None,
                          metadata: Dict[str, Any] = None) -> str:
        """שמירת זיכרון חדש"""
        memory_id = f"mem_{user_id}_{int(datetime.now().timestamp())}"
        
        # יצירת embedding
        embedding = self.generate_embedding(content)
        
        # שמירה בVectorDB
        self.vector_collection.add(
            embeddings=[embedding.tolist()],
            documents=[content],
            metadatas=[{
                "user_id": user_id,
                "memory_type": memory_type.value,
                "importance": importance,
                "emotional_context": emotional_context.value if emotional_context else None,
                "created_at": datetime.now().isoformat()
            }],
            ids=[memory_id]
        )
        
        # שמירה בSQL
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO memories (id, user_id, content, memory_type, importance, 
                                emotional_context, metadata, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id, user_id, content, memory_type.value, importance,
            emotional_context.value if emotional_context else None,
            json.dumps(metadata) if metadata else "{}",
            memory_id
        ))
        
        conn.commit()
        conn.close()
        
        print(f"💾 זיכרון נשמר: {memory_type.value} - {content[:50]}...")
        return memory_id
    
    async def retrieve_relevant_memories(self, user_id: int, query: str, 
                                       limit: int = 10, min_relevance: float = 0.3) -> List[Memory]:
        """שליפת זיכרונות רלוונטיים"""
        # חיפוש סמנטי
        query_embedding = self.generate_embedding(query)
        
        results = self.vector_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit * 2,  # מביא יותר לפילטור
            where={"user_id": user_id}
        )
        
        # פילטור לפי רלוונטיות
        relevant_memories = []
        
        if results['documents']:
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                relevance = 1 - distance  # המרה למדד רלוונטיות
                
                if relevance >= min_relevance:
                    memory = Memory(
                        id=results['ids'][0][i],
                        user_id=user_id,
                        content=doc,
                        memory_type=MemoryType(metadata['memory_type']),
                        importance=metadata['importance'],
                        emotional_context=EmotionalState(metadata['emotional_context']) if metadata.get('emotional_context') else None,
                        created_at=datetime.fromisoformat(metadata['created_at']),
                        last_accessed=datetime.now(),
                        access_count=0,
                        metadata={"relevance": relevance}
                    )
                    relevant_memories.append(memory)
        
        # מיון לפי חשיבות ורלוונטיות
        relevant_memories.sort(key=lambda m: m.importance * m.metadata['relevance'], reverse=True)
        
        return relevant_memories[:limit]
    
    async def get_conversation_context(self, user_id: int) -> ConversationContext:
        """קבלת הקשר שיחה מלא"""
        if user_id in self.context_cache:
            return self.context_cache[user_id]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # שליפת שיחות אחרונות
        cursor.execute("""
            SELECT message, response, emotional_context, topic
            FROM conversations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id,))
        
        recent_conversations = cursor.fetchall()
        
        # שליפת העדפות
        cursor.execute("""
            SELECT preferences, personality_traits, emotional_patterns
            FROM user_profiles
            WHERE user_id = ?
        """, (user_id,))
        
        profile_data = cursor.fetchone()
        
        conn.close()
        
        # בניית הקשר
        context = ConversationContext(
            user_id=user_id,
            current_topic=recent_conversations[0][3] if recent_conversations else None,
            emotional_state=EmotionalState(recent_conversations[0][2]) if recent_conversations and recent_conversations[0][2] else EmotionalState.CALM,
            recent_memories=[],
            conversation_flow=[conv[0] for conv in recent_conversations[:5]],
            user_preferences=json.loads(profile_data[0]) if profile_data and profile_data[0] else {}
        )
        
        self.context_cache[user_id] = context
        return context
    
    async def update_emotional_state(self, user_id: int, emotional_state: EmotionalState):
        """עדכון מצב רגשי"""
        if user_id in self.context_cache:
            self.context_cache[user_id].emotional_state = emotional_state
        
        # שמירת זיכרון רגשי
        await self.store_memory(
            user_id=user_id,
            content=f"מצב רגשי: {emotional_state.value}",
            memory_type=MemoryType.EMOTIONAL_STATE,
            importance=0.7,
            emotional_context=emotional_state
        )
    
    async def learn_user_preference(self, user_id: int, preference_key: str, preference_value: str):
        """למידת העדפת משתמש"""
        await self.store_memory(
            user_id=user_id,
            content=f"העדפה: {preference_key} = {preference_value}",
            memory_type=MemoryType.PREFERENCE,
            importance=0.8,
            metadata={"key": preference_key, "value": preference_value}
        )
        
        # עדכון פרופיל
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_profiles (user_id, preferences, updated_at)
            VALUES (?, ?, ?)
        """, (user_id, json.dumps({preference_key: preference_value}), datetime.now()))
        
        conn.commit()
        conn.close()
    
    async def get_memory_summary(self, user_id: int) -> Dict[str, Any]:
        """סיכום זיכרון המשתמש"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # סטטיסטיקות בסיסיות
        cursor.execute("""
            SELECT memory_type, COUNT(*), AVG(importance)
            FROM memories
            WHERE user_id = ?
            GROUP BY memory_type
        """, (user_id,))
        
        memory_stats = cursor.fetchall()
        
        # שיחות אחרונות
        cursor.execute("""
            SELECT COUNT(*), MAX(created_at)
            FROM conversations
            WHERE user_id = ?
        """, (user_id,))
        
        conversation_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "total_memories": sum(stat[1] for stat in memory_stats),
            "memory_breakdown": {stat[0]: {"count": stat[1], "avg_importance": stat[2]} for stat in memory_stats},
            "total_conversations": conversation_stats[0],
            "last_conversation": conversation_stats[1],
            "emotional_patterns": await self.analyze_emotional_patterns(user_id)
        }
    
    async def analyze_emotional_patterns(self, user_id: int) -> Dict[str, Any]:
        """ניתוח דפוסים רגשיים"""
        emotional_memories = await self.retrieve_relevant_memories(
            user_id, "רגש מצב רוח", limit=50
        )
        
        # ניתוח דפוסים
        emotions_count = {}
        for memory in emotional_memories:
            if memory.emotional_context:
                emotion = memory.emotional_context.value
                emotions_count[emotion] = emotions_count.get(emotion, 0) + 1
        
        return {
            "dominant_emotions": emotions_count,
            "emotional_stability": len(set(emotions_count.keys())) if emotions_count else 0,
            "recent_emotional_trend": "positive" if emotions_count.get("happy", 0) > emotions_count.get("sad", 0) else "negative"
        }
    
    def clear_context_cache(self, user_id: int = None):
        """ניקוי cache הקשר"""
        if user_id:
            self.context_cache.pop(user_id, None)
        else:
            self.context_cache.clear()
    
    async def cleanup_old_memories(self, days_old: int = 30, min_importance: float = 0.3):
        """ניקוי זיכרונות ישנים ולא חשובים"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # מציאת זיכרונות לניקוי
        cursor.execute("""
            SELECT id FROM memories
            WHERE created_at < ? AND importance < ? AND access_count < 2
        """, (cutoff_date, min_importance))
        
        old_memories = cursor.fetchall()
        
        # מחיקה מSQL
        cursor.execute("""
            DELETE FROM memories
            WHERE created_at < ? AND importance < ? AND access_count < 2
        """, (cutoff_date, min_importance))
        
        conn.commit()
        conn.close()
        
        # מחיקה מVector DB
        if old_memories:
            memory_ids = [mem[0] for mem in old_memories]
            self.vector_collection.delete(ids=memory_ids)
            
            print(f"🧹 נוקו {len(old_memories)} זיכרונות ישנים")
    
    async def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """תובנות מעמיקות על המשתמש"""
        context = await self.get_conversation_context(user_id)
        summary = await self.get_memory_summary(user_id)
        
        return {
            "user_profile": {
                "emotional_state": context.emotional_state.value,
                "preferences": context.user_preferences,
                "current_topic": context.current_topic
            },
            "memory_analysis": summary,
            "conversation_patterns": {
                "recent_topics": [topic for topic in context.conversation_flow if topic],
                "interaction_frequency": summary["total_conversations"],
                "engagement_level": "high" if summary["total_conversations"] > 10 else "medium"
            },
            "recommendations": self.generate_interaction_recommendations(summary, context)
        }
    
    def generate_interaction_recommendations(self, summary: Dict, context: ConversationContext) -> List[str]:
        """המלצות לאינטראקציה טובה יותר"""
        recommendations = []
        
        # בדיקת דפוסים רגשיים
        emotional_patterns = summary.get("emotional_patterns", {})
        if emotional_patterns.get("recent_emotional_trend") == "negative":
            recommendations.append("הצע תמיכה רגשית או פעילות מעודדת")
        
        # בדיקת תדירות אינטראקציה
        if summary["total_conversations"] < 5:
            recommendations.append("עודד שיחה נוספת כדי ללמוד על המשתמש")
        
        # בדיקת העדפות
        if not context.user_preferences:
            recommendations.append("שאל על תחומי עניין והעדפות")
        
        return recommendations

# יצירת instance global
memory_system = AdvancedMemorySystem()

# פונקציות עזר
async def remember_conversation(user_id: int, message: str, response: str, emotional_context: EmotionalState = None):
    """שמירת שיחה עם הקשר רגשי"""
    await memory_system.store_memory(
        user_id=user_id,
        content=f"שיחה: {message} -> {response}",
        memory_type=MemoryType.CONVERSATION,
        importance=0.6,
        emotional_context=emotional_context
    )

async def learn_about_user(user_id: int, fact: str, importance: float = 0.8):
    """למידת עובדה על המשתמש"""
    await memory_system.store_memory(
        user_id=user_id,
        content=fact,
        memory_type=MemoryType.PERSONAL_FACT,
        importance=importance
    )

async def get_smart_context(user_id: int, current_message: str) -> Dict[str, Any]:
    """קבלת הקשר חכם לתגובה"""
    context = await memory_system.get_conversation_context(user_id)
    relevant_memories = await memory_system.retrieve_relevant_memories(user_id, current_message)
    
    return {
        "emotional_state": context.emotional_state.value,
        "relevant_memories": [mem.content for mem in relevant_memories[:3]],
        "user_preferences": context.user_preferences,
        "recent_topics": context.conversation_flow[:3],
        "insights": await memory_system.get_user_insights(user_id)
    }
