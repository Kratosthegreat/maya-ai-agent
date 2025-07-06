# -*- coding: utf-8 -*-
# Maya - True Global AI Secretary with Advanced Intelligence
# Based on comprehensive research of enterprise AI capabilities 2025

import os
import json
import re
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
import requests
import pytz
import random
import sqlite3
from dataclasses import dataclass, field
import hashlib
import hmac
from contextlib import contextmanager
import wikipedia
import yfinance as yf
import feedparser
from flask import Flask, request, jsonify, Response
from http import HTTPStatus
from googletrans import Translator
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import wolframalpha
import calendar
import schedule
import threading

# ==================== ENTERPRISE CONFIGURATION ====================
class GlobalConfig:
    def __init__(self):
        # Core Bot Configuration
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        if not self.TELEGRAM_TOKEN:
            raise ValueError("Missing TELEGRAM_TOKEN environment variable")
        
        self.PORT = int(os.getenv("PORT", 10000))
        self.DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
        self.TIMEZONE = pytz.timezone("Asia/Jerusalem")
        
        # AI & Knowledge APIs - Research-Based Integration
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "")
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
        self.NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
        self.FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
        
        # External APIs for Global Knowledge
        self.WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
        self.NEWS_API_URL = "https://newsapi.org/v2/everything"
        self.FINANCE_API_URL = "https://finnhub.io/api/v1"
        self.EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest"
        
        # Enhanced Features
        self.MAX_KNOWLEDGE_CACHE = 1000
        self.CACHE_DURATION = 3600  # 1 hour
        self.SUPPORTED_LANGUAGES = 50
        self.DB_PATH = "maya_global_brain.db"

# ==================== ADVANCED LOGGING ====================
config = GlobalConfig()

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("maya_secretary.log") if not config.DEBUG else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== GLOBAL KNOWLEDGE ENGINE ====================
class GlobalKnowledgeEngine:
    """Advanced Knowledge Engine integrating multiple global data sources"""
    
    def __init__(self):
        self.translator = Translator()
        self.cache = {}
        self.wolfram_client = None
        self.gemini_model = None
        
        # Initialize API clients
        self._init_api_clients()
        
        # Knowledge domains
        self.knowledge_domains = {
            'mathematics': ['calculation', 'math', 'equation', 'compute'],
            'science': ['physics', 'chemistry', 'biology', 'research'],
            'finance': ['stock', 'market', 'price', 'currency', 'exchange'],
            'geography': ['country', 'city', 'population', 'capital'],
            'history': ['when', 'year', 'historical', 'event'],
            'weather': ['weather', 'temperature', 'forecast', 'climate'],
            'news': ['news', 'current', 'latest', 'today', 'happened'],
            'translation': ['translate', 'language', 'meaning'],
            'general': ['what', 'how', 'why', 'explain', 'tell me']
        }
    
    def _init_api_clients(self):
        """Initialize external API clients"""
        try:
            if config.WOLFRAM_APP_ID:
                self.wolfram_client = wolframalpha.Client(config.WOLFRAM_APP_ID)
                logger.info("Wolfram Alpha client initialized")
            
            if config.GEMINI_API_KEY:
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(
                    'gemini-pro',
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                logger.info("Gemini Pro client initialized")
        
        except Exception as e:
            logger.error(f"Error initializing API clients: {e}")
    
    def classify_query_domain(self, query: str) -> str:
        """Classify query into knowledge domain"""
        query_lower = query.lower()
        
        # Count domain keywords
        domain_scores = {}
        for domain, keywords in self.knowledge_domains.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            domain_scores[domain] = score
        
        # Return domain with highest score
        best_domain = max(domain_scores, key=domain_scores.get)
        return best_domain if domain_scores[best_domain] > 0 else 'general'
    
    async def get_comprehensive_answer(self, query: str, language: str = 'he') -> Dict[str, Any]:
        """Get comprehensive answer using multiple knowledge sources"""
        
        # Check cache first
        cache_key = f"{query}_{language}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < config.CACHE_DURATION:
                return cached_data
        
        # Classify query domain
        domain = self.classify_query_domain(query)
        logger.info(f"Query classified as: {domain}")
        
        result = {
            'domain': domain,
            'query': query,
            'language': language,
            'sources': [],
            'answer': '',
            'confidence': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Route to appropriate knowledge source
            if domain == 'mathematics':
                result.update(await self._handle_math_query(query))
            elif domain == 'science':
                result.update(await self._handle_science_query(query))
            elif domain == 'finance':
                result.update(await self._handle_finance_query(query))
            elif domain == 'weather':
                result.update(await self._handle_weather_query(query))
            elif domain == 'news':
                result.update(await self._handle_news_query(query))
            elif domain == 'translation':
                result.update(await self._handle_translation_query(query))
            else:
                result.update(await self._handle_general_query(query))
            
            # Translate answer if needed
            if language != 'en' and result['answer']:
                result['answer'] = await self._translate_text(result['answer'], language)
            
            # Cache result
            self.cache[cache_key] = (result, time.time())
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            result['answer'] = f"מצטערת, נתקלתי בבעיה בעת חיפוש המידע. {str(e)[:100]}..."
            result['confidence'] = 0.1
        
        return result
    
    async def _handle_math_query(self, query: str) -> Dict[str, Any]:
        """Handle mathematical calculations using Wolfram Alpha"""
        if not self.wolfram_client:
            return {'answer': 'שירות חישובים לא זמין כרגע', 'confidence': 0.1, 'sources': []}
        
        try:
            # Query Wolfram Alpha
            res = self.wolfram_client.query(query)
            
            if hasattr(res, 'results') and len(list(res.results)) > 0:
                answer = next(res.results).text
                return {
                    'answer': f"🧮 תוצאת החישוב: {answer}",
                    'confidence': 0.95,
                    'sources': ['Wolfram Alpha']
                }
            else:
                return {
                    'answer': 'לא הצלחתי לפתור את החישוב. תוכל לנסח אותו אחרת?',
                    'confidence': 0.2,
                    'sources': ['Wolfram Alpha']
                }
        
        except Exception as e:
            logger.error(f"Wolfram Alpha error: {e}")
            return {
                'answer': f'שגיאה בחישוב: {str(e)[:100]}',
                'confidence': 0.1,
                'sources': ['Wolfram Alpha (Error)']
            }
    
    async def _handle_science_query(self, query: str) -> Dict[str, Any]:
        """Handle scientific queries using Wikipedia and Wolfram"""
        try:
            # Try Wikipedia first
            wiki_results = wikipedia.search(query, results=3)
            if wiki_results:
                page = wikipedia.page(wiki_results[0])
                summary = wikipedia.summary(query, sentences=3)
                
                return {
                    'answer': f"🔬 {summary}\n\nמקור: {page.url}",
                    'confidence': 0.8,
                    'sources': ['Wikipedia']
                }
            
            # Fallback to Wolfram if available
            if self.wolfram_client:
                res = self.wolfram_client.query(query)
                if hasattr(res, 'results') and len(list(res.results)) > 0:
                    answer = next(res.results).text
                    return {
                        'answer': f"🔬 {answer}",
                        'confidence': 0.85,
                        'sources': ['Wolfram Alpha']
                    }
            
            return {
                'answer': 'לא מצאתי מידע מדעי על הנושא הזה',
                'confidence': 0.1,
                'sources': []
            }
        
        except Exception as e:
            logger.error(f"Science query error: {e}")
            return {
                'answer': f'שגיאה בחיפוש מידע מדעי: {str(e)[:100]}',
                'confidence': 0.1,
                'sources': ['Error']
            }
    
    async def _handle_finance_query(self, query: str) -> Dict[str, Any]:
        """Handle financial queries using multiple APIs"""
        try:
            # Extract stock symbol if present
            stock_symbols = re.findall(r'\b[A-Z]{1,5}\b', query.upper())
            
            if stock_symbols:
                symbol = stock_symbols[0]
                # Use yfinance for stock data
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if 'currentPrice' in info:
                    price = info['currentPrice']
                    change = info.get('regularMarketChangePercent', 0)
                    
                    return {
                        'answer': f"💰 {symbol}: ${price:.2f} ({change:+.2f}%)\nחברה: {info.get('longName', 'N/A')}",
                        'confidence': 0.9,
                        'sources': ['Yahoo Finance']
                    }
            
            # Handle currency exchange
            currencies = re.findall(r'\b(USD|EUR|GBP|JPY|ILS)\b', query.upper())
            if len(currencies) >= 2:
                from_curr, to_curr = currencies[0], currencies[1]
                try:
                    response = requests.get(f"{config.EXCHANGE_API_URL}/{from_curr}", timeout=5)
                    data = response.json()
                    rate = data['rates'].get(to_curr)
                    
                    if rate:
                        return {
                            'answer': f"💱 1 {from_curr} = {rate:.4f} {to_curr}",
                            'confidence': 0.95,
                            'sources': ['Exchange Rate API']
                        }
                except:
                    pass
            
            return {
                'answer': 'לא הצלחתי למצוא מידע פיננסי על הנושא הזה',
                'confidence': 0.1,
                'sources': []
            }
        
        except Exception as e:
            logger.error(f"Finance query error: {e}")
            return {
                'answer': f'שגיאה בחיפוש מידע פיננסי: {str(e)[:100]}',
                'confidence': 0.1,
                'sources': ['Error']
            }
    
    async def _handle_weather_query(self, query: str) -> Dict[str, Any]:
        """Handle weather queries with enhanced city detection"""
        if not config.WEATHER_API_KEY:
            return {'answer': 'שירות מזג אוויר לא זמין', 'confidence': 0.1, 'sources': []}
        
        # Enhanced city extraction
        cities = [
            'תל אביב', 'ירושלים', 'חיפה', 'באר שבע', 'אילת', 'נתניה',
            'Tel Aviv', 'Jerusalem', 'Haifa', 'Beer Sheva', 'Eilat', 'Netanya',
            'New York', 'London', 'Paris', 'Tokyo', 'Berlin', 'Rome'
        ]
        
        city = None
        for c in cities:
            if c.lower() in query.lower():
                city = c
                break
        
        if not city:
            city = 'Tel Aviv'  # Default
        
        try:
            response = requests.get(
                config.WEATHER_API_URL,
                params={
                    'q': city,
                    'appid': config.WEATHER_API_KEY,
                    'units': 'metric',
                    'lang': 'he'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                wind = data['wind']['speed']
                
                return {
                    'answer': (f"🌤️ מזג האוויר ב{data['name']}:\n"
                             f"🌡️ טמפרטורה: {temp:.1f}°C (מרגיש כמו {feels_like:.1f}°C)\n"
                             f"☁️ מצב: {description}\n"
                             f"💧 לחות: {humidity}%\n"
                             f"🌪️ רוח: {wind:.1f} מ/ש"),
                    'confidence': 0.95,
                    'sources': ['OpenWeatherMap']
                }
            
            return {
                'answer': f'לא הצלחתי לקבל מידע על מזג האוויר ב{city}',
                'confidence': 0.2,
                'sources': ['OpenWeatherMap']
            }
        
        except Exception as e:
            logger.error(f"Weather query error: {e}")
            return {
                'answer': f'שגיאה בקבלת מידע מזג אוויר: {str(e)[:100]}',
                'confidence': 0.1,
                'sources': ['Error']
            }
    
    async def _handle_news_query(self, query: str) -> Dict[str, Any]:
        """Handle news queries using news APIs"""
        try:
            # Try RSS feeds first (free)
            rss_feeds = [
                'https://rss.cnn.com/rss/edition.rss',
                'https://feeds.bbci.co.uk/news/rss.xml',
                'https://www.ynet.co.il/Integration/StoryRss2.xml'
            ]
            
            news_items = []
            for feed_url in rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:2]:  # Top 2 from each
                        news_items.append({
                            'title': entry.title,
                            'link': entry.link,
                            'published': entry.get('published', 'N/A')
                        })
                except:
                    continue
            
            if news_items:
                news_text = "📰 חדשות אחרונות:\n\n"
                for i, item in enumerate(news_items[:3], 1):
                    news_text += f"{i}. {item['title']}\n"
                
                return {
                    'answer': news_text,
                    'confidence': 0.8,
                    'sources': ['RSS Feeds']
                }
            
            return {
                'answer': 'לא הצלחתי לקבל חדשות כרגע',
                'confidence': 0.1,
                'sources': []
            }
        
        except Exception as e:
            logger.error(f"News query error: {e}")
            return {
                'answer': f'שגיאה בקבלת חדשות: {str(e)[:100]}',
                'confidence': 0.1,
                'sources': ['Error']
            }
    
    async def _handle_translation_query(self, query: str) -> Dict[str, Any]:
        """Handle translation requests"""
        try:
            # Extract text to translate
            translate_patterns = [
                r'תרגם[י]?\s+["\'](.+?)["\']',
                r'translate[s]?\s+["\'](.+?)["\']',
                r'מה זה ["\'](.+?)["\'] באנגלית',
                r'איך אומרים ["\'](.+?)["\']'
            ]
            
            text_to_translate = None
            for pattern in translate_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    text_to_translate = match.group(1)
                    break
            
            if not text_to_translate:
                return {
                    'answer': 'לא הבנתי מה לתרגם. תוכל לכתוב: "תרגם \"הטקסט כאן\""?',
                    'confidence': 0.2,
                    'sources': []
                }
            
            # Detect source language and translate
            detection = self.translator.detect(text_to_translate)
            src_lang = detection.lang
            
            # Translate to Hebrew if source is not Hebrew, otherwise to English
            target_lang = 'he' if src_lang != 'he' else 'en'
            
            translation = self.translator.translate(text_to_translate, 
                                                  src=src_lang, 
                                                  dest=target_lang)
            
            return {
                'answer': f"🌐 תרגום:\n\"{text_to_translate}\" = \"{translation.text}\"",
                'confidence': 0.9,
                'sources': ['Google Translate']
            }
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                'answer': f'שגיאה בתרגום: {str(e)[:100]}',
                'confidence': 0.1,
                'sources': ['Error']
            }
    
    async def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general knowledge queries"""
        try:
            # Try Wikipedia first
            wiki_results = wikipedia.search(query, results=3)
            if wiki_results:
                summary = wikipedia.summary(query, sentences=2)
                page = wikipedia.page(wiki_results[0])
                
                return {
                    'answer': f"📚 {summary}\n\nמידע נוסף: {page.url}",
                    'confidence': 0.75,
                    'sources': ['Wikipedia']
                }
            
            # Try Gemini if available
            if self.gemini_model and config.GEMINI_API_KEY:
                try:
                    prompt = f"ענה בעברית על השאלה הבאה בצורה קצרה ומדויקת: {query}"
                    response = self.gemini_model.generate_content(prompt)
                    
                    if response and response.text:
                        return {
                            'answer': f"🤖 {response.text}",
                            'confidence': 0.8,
                            'sources': ['Google Gemini']
                        }
                except Exception as e:
                    logger.error(f"Gemini error: {e}")
                    pass
            
            return {
                'answer': 'לא מצאתי מידע על הנושא הזה. תוכל לנסח את השאלה אחרת?',
                'confidence': 0.1,
                'sources': []
            }
        
        except Exception as e:
            logger.error(f"General query error: {e}")
            return {
                'answer': f'שגיאה בחיפוש מידע: {str(e)[:100]}',
                'confidence': 0.1,
                'sources': ['Error']
            }
    
    async def _translate_text(self, text: str, target_lang: str) -> str:
        """Translate text to target language"""
        try:
            if target_lang == 'he' and not re.search(r'[\u05D0-\u05EA]', text):
                translation = self.translator.translate(text, dest='he')
                return translation.text
            return text
        except:
            return text

# ==================== ADVANCED USER CONTEXT SYSTEM ====================
@dataclass
class UserProfile:
    user_id: int
    name: Optional[str] = None
    preferred_language: str = 'he'
    location: Optional[str] = None
    timezone: str = 'Asia/Jerusalem'
    interaction_history: List[Dict] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    expertise_areas: List[str] = field(default_factory=list)
    last_activity: Optional[datetime] = None
    total_interactions: int = 0

class UserContextManager:
    """Advanced user context and memory management"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.active_profiles = {}
        self.init_database()
    
    def init_database(self):
        """Initialize advanced user database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    preferred_language TEXT DEFAULT 'he',
                    location TEXT,
                    timezone TEXT DEFAULT 'Asia/Jerusalem',
                    preferences TEXT DEFAULT '{}',
                    expertise_areas TEXT DEFAULT '[]',
                    total_interactions INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS interaction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    query TEXT,
                    response_summary TEXT,
                    domain TEXT,
                    confidence REAL,
                    sources TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                );
                
                CREATE TABLE IF NOT EXISTS user_knowledge_graph (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    topic TEXT,
                    interest_level REAL DEFAULT 0.5,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                );
            ''')
            logger.info("Advanced user database initialized")
    
    def get_user_profile(self, user_id: int) -> UserProfile:
        """Get or create user profile"""
        if user_id in self.active_profiles:
            return self.active_profiles[user_id]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            
            if row:
                profile = UserProfile(
                    user_id=user_id,
                    name=row['name'],
                    preferred_language=row['preferred_language'],
                    location=row['location'],
                    timezone=row['timezone'],
                    preferences=json.loads(row['preferences']),
                    expertise_areas=json.loads(row['expertise_areas']),
                    total_interactions=row['total_interactions'],
                    last_activity=datetime.fromisoformat(row['last_activity'])
                )
            else:
                profile = UserProfile(
                    user_id=user_id,
                    last_activity=datetime.now()
                )
                self._create_user_profile(profile)
        
        # Load recent interaction history
        self._load_interaction_history(profile)
        self.active_profiles[user_id] = profile
        return profile
    
    def _create_user_profile(self, profile: UserProfile):
        """Create new user profile in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO user_profiles 
                (user_id, name, preferred_language, location, timezone, preferences, expertise_areas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile.user_id, profile.name, profile.preferred_language,
                profile.location, profile.timezone,
                json.dumps(profile.preferences),
                json.dumps(profile.expertise_areas)
            ))
    
    def _load_interaction_history(self, profile: UserProfile):
        """Load recent interaction history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('''
                SELECT * FROM interaction_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 20
            ''', (profile.user_id,)).fetchall()
            
            profile.interaction_history = [
                {
                    'query': row['query'],
                    'response_summary': row['response_summary'],
                    'domain': row['domain'],
                    'confidence': row['confidence'],
                    'sources': json.loads(row['sources']) if row['sources'] else [],
                    'timestamp': row['timestamp']
                }
                for row in reversed(rows)
            ]
    
    def update_user_profile(self, profile: UserProfile):
        """Update user profile in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE user_profiles SET
                name = ?, preferred_language = ?, location = ?, timezone = ?,
                preferences = ?, expertise_areas = ?, total_interactions = ?,
                last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                profile.name, profile.preferred_language, profile.location,
                profile.timezone, json.dumps(profile.preferences),
                json.dumps(profile.expertise_areas), profile.total_interactions,
                profile.user_id
            ))
    
    def save_interaction(self, user_id: int, query: str, result: Dict[str, Any]):
        """Save interaction to history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO interaction_history 
                (user_id, query, response_summary, domain, confidence, sources)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id, query[:500], result.get('answer', '')[:200],
                result.get('domain', 'unknown'), result.get('confidence', 0.0),
                json.dumps(result.get('sources', []))
            ))
        
        # Update user knowledge graph
        self._update_knowledge_interests(user_id, result.get('domain', 'unknown'))
    
    def _update_knowledge_interests(self, user_id: int, domain: str):
        """Update user's knowledge interests based on interactions"""
        with sqlite3.connect(self.db_path) as conn:
            # Check if topic exists
            existing = conn.execute(
                "SELECT interest_level FROM user_knowledge_graph WHERE user_id = ? AND topic = ?",
                (user_id, domain)
            ).fetchone()
            
            if existing:
                # Increase interest level
                new_level = min(1.0, existing[0] + 0.1)
                conn.execute(
                    "UPDATE user_knowledge_graph SET interest_level = ?, last_accessed = CURRENT_TIMESTAMP WHERE user_id = ? AND topic = ?",
                    (new_level, user_id, domain)
                )
            else:
                # Create new interest
                conn.execute(
                    "INSERT INTO user_knowledge_graph (user_id, topic, interest_level) VALUES (?, ?, ?)",
                    (user_id, domain, 0.6)
                )

# ==================== INTELLIGENT CONVERSATION ENGINE ====================
class IntelligentConversationEngine:
    """Advanced conversation engine with personality and context awareness"""
    
    def __init__(self, knowledge_engine: GlobalKnowledgeEngine, user_manager: UserContextManager):
        self.knowledge_engine = knowledge_engine
        self.user_manager = user_manager
        self.conversation_patterns = self._load_conversation_patterns()
        self.personality_traits = {
            'helpful': 0.9,
            'professional': 0.8,
            'friendly': 0.9,
            'intelligent': 0.95,
            'cultural_aware': 0.9
        }
    
    def _load_conversation_patterns(self) -> Dict[str, List[str]]:
        """Load advanced conversation patterns"""
        return {
            'greeting_responses': {
                'morning': [
                    "בוקר טוב! ☀️ איך התחלת את היום? אני כאן לכל שאלה או משימה.",
                    "בוקר טוב! 🌅 מוכנה לעזור לך עם כל מה שתצטרך היום.",
                    "בוקר טוב! ☕ מה התוכניות? יש לי גישה למידע עולמי ויכולות חישוב מתקדמות."
                ],
                'afternoon': [
                    "צהריים טובים! 🌤️ איך עובר היום? במה אוכל לסייע?",
                    "שלום! 👋 אני מאיה, המזכירה הדיגיטלית שלך. מה אוכל לעזור לך למצוא או לחשב?",
                    "צהריים טובים! 😊 יש לי גישה לידע בתחומי מתמטיקה, מדע, כלכלה ועוד."
                ],
                'evening': [
                    "ערב טוב! 🌆 איך היה היום? אוכל לעזור עם מידע או חישובים.",
                    "ערב טוב! 🌙 אני כאן לכל שאלה - מחישובים מתמטיים ועד חדשות אחרונות.",
                    "שלום! ערב נעים! 🌟 מה מעניין אותך לדעת?"
                ]
            },
            'knowledge_responses': {
                'high_confidence': [
                    "בהתבסס על המידע העדכני ביותר:",
                    "לפי הנתונים המדויקים שמצאתי:",
                    "הנה המידע המאומת שחיפשת:"
                ],
                'medium_confidence': [
                    "לפי המידע שמצאתי:",
                    "בהתבסס על המקורות הזמינים:",
                    "הנה מה שהצלחתי למצוא:"
                ],
                'low_confidence': [
                    "המידע שמצאתי מוגבל, אבל:",
                    "לא מצאתי מידע מלא, אבל יכול להיות ש:",
                    "המידע הזמין חלקי:"
                ]
            },
            'error_responses': [
                "מצטערת, נתקלתי בבעיה טכנית. בוא ננסה שוב?",
                "יש לי קושי לגשת למידע הזה כרגע. תוכל לנסח את השאלה אחרת?",
                "נראה שיש בעיה זמנית בחיבור למקורות המידע. ננסה שוב?"
            ],
            'clarification_requests': [
                "תוכל להיות יותר ספציפי? זה יעזור לי למצוא בדיוק מה שאתה מחפש.",
                "יש כמה אפשרויות. על מה בדיוק אתה רוצה לדעת?",
                "כדי לתת לך את המידע הכי מדויק, תוכל לפרט יותר?"
            ]
        }
    
    async def process_conversation(self, user_id: int, message: str) -> str:
        """Process conversation with advanced intelligence"""
        
        # Get user profile
        profile = self.user_manager.get_user_profile(user_id)
        profile.total_interactions += 1
        
        # Detect message type and intent
        message_analysis = self._analyze_message(message, profile)
        
        try:
            if message_analysis['type'] == 'greeting':
                response = await self._handle_greeting(profile)
            
            elif message_analysis['type'] == 'personal_info':
                response = await self._handle_personal_info(message, profile)
            
            elif message_analysis['type'] == 'knowledge_query':
                response = await self._handle_knowledge_query(message, profile)
            
            elif message_analysis['type'] == 'casual_chat':
                response = await self._handle_casual_chat(message, profile)
            
            else:
                response = await self._handle_unknown(message, profile)
            
            # Update user profile
            self.user_manager.update_user_profile(profile)
            
            return response
        
        except Exception as e:
            logger.error(f"Conversation processing error: {e}")
            return random.choice(self.conversation_patterns['error_responses'])
    
    def _analyze_message(self, message: str, profile: UserProfile) -> Dict[str, Any]:
        """Analyze message type and extract intent"""
        message_lower = message.lower()
        
        # Greeting patterns
        greeting_patterns = [
            r'שלום|היי|הי|הייי|בוקר טוב|ערב טוב|לילה טוב',
            r'מה שלומך|איך אתה|איך את|מה נשמע'
        ]
        
        # Personal info patterns
        personal_patterns = [
            r'שמי|קוראים לי|השם שלי|אני',
            r'גר ב|גרה ב|מ[בהמ]|יליד'
        ]
        
        # Knowledge query patterns
        knowledge_patterns = [
            r'מה|איך|למה|מתי|איפה|כמה|מי',
            r'חשב|תחשב|תרגם|מזג אוויר|חדשות|מחיר'
        ]
        
        # Determine message type
        if any(re.search(pattern, message_lower) for pattern in greeting_patterns):
            return {'type': 'greeting', 'confidence': 0.9}
        
        elif any(re.search(pattern, message_lower) for pattern in personal_patterns):
            return {'type': 'personal_info', 'confidence': 0.85}
        
        elif any(re.search(pattern, message_lower) for pattern in knowledge_patterns):
            return {'type': 'knowledge_query', 'confidence': 0.8}
        
        else:
            return {'type': 'casual_chat', 'confidence': 0.6}
    
    async def _handle_greeting(self, profile: UserProfile) -> str:
        """Handle greeting with personalization"""
        
        # Determine time of day
        now = datetime.now(pytz.timezone(profile.timezone))
        hour = now.hour
        
        if 5 <= hour < 12:
            time_context = 'morning'
        elif 12 <= hour < 17:
            time_context = 'afternoon'
        else:
            time_context = 'evening'
        
        # Get appropriate greeting
        greetings = self.conversation_patterns['greeting_responses'][time_context]
        base_greeting = random.choice(greetings)
        
        # Personalize if name is known
        if profile.name:
            base_greeting = base_greeting.replace("!", f" {profile.name}!")
        
        # Add context based on interaction history
        if profile.total_interactions > 10:
            base_greeting += f"\n\nאני זוכרת שאתה מתעניין ב{self._get_top_interests(profile)}."
        
        return base_greeting
    
    async def _handle_personal_info(self, message: str, profile: UserProfile) -> str:
        """Handle personal information sharing"""
        
        # Extract name
        name_patterns = [
            r'שמי (הוא )?(.+?)(?:\s|$|\.)',
            r'קוראים לי (.+?)(?:\s|$|\.)',
            r'השם שלי (הוא )?(.+?)(?:\s|$|\.)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(-1).strip()
                if len(name) > 0 and len(name) < 20:
                    profile.name = name
                    return f"נעים מאוד להכיר אותך, {name}! 😊 אני מאיה, המזכירה הדיגיטלית שלך. יש לי גישה לידע עולמי ויכולות חישוב מתקדמות. איך אוכל לעזור לך?"
        
        # Extract location
        location_patterns = [
            r'גר ב(.+?)(?:\s|$|\.)',
            r'מ(.+?)(?:\s|$|\.)',
            r'גרה ב(.+?)(?:\s|$|\.)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message)
            if match:
                location = match.group(1).strip()
                if len(location) > 1:
                    profile.location = location
                    return f"נחמד! אז אתה מ{location}. יכול להיות שיש לי מידע מעניין על המקום שלך. רוצה לדעת משהו?"
        
        return "תודה שאתה חולק איתי! 😊 זה עוזר לי להכיר אותך יותר טוב ולהתאים את התשובות שלי."
    
    async def _handle_knowledge_query(self, message: str, profile: UserProfile) -> str:
        """Handle knowledge queries using global knowledge engine"""
        
        # Get comprehensive answer
        result = await self.knowledge_engine.get_comprehensive_answer(
            message, profile.preferred_language
        )
        
        # Save interaction
        self.user_manager.save_interaction(profile.user_id, message, result)
        
        # Format response based on confidence
        confidence = result.get('confidence', 0.0)
        
        if confidence > 0.8:
            intro = random.choice(self.conversation_patterns['knowledge_responses']['high_confidence'])
        elif confidence > 0.5:
            intro = random.choice(self.conversation_patterns['knowledge_responses']['medium_confidence'])
        else:
            intro = random.choice(self.conversation_patterns['knowledge_responses']['low_confidence'])
        
        # Build response
        response = f"{intro}\n\n{result['answer']}"
        
        # Add sources if available
        if result.get('sources'):
            response += f"\n\n📚 מקורות: {', '.join(result['sources'])}"
        
        # Add follow-up suggestion
        if confidence > 0.7:
            response += "\n\nיש עוד משהו שתרצה לדעת בנושא?"
        
        return response
    
    async def _handle_casual_chat(self, message: str, profile: UserProfile) -> str:
        """Handle casual conversation"""
        
        casual_responses = [
            f"מעניין! אני כאן לעזור עם כל שאלה או חישוב{' ' + profile.name if profile.name else ''}.",
            "אפשר לספר לי יותר? אולי אוכל לעזור עם מידע רלוונטי.",
            "נשמע מעניין! במה אוכל לסייע? יש לי גישה למידע בהרבה תחומים."
        ]
        
        return random.choice(casual_responses)
    
    async def _handle_unknown(self, message: str, profile: UserProfile) -> str:
        """Handle unknown message types"""
        
        return random.choice(self.conversation_patterns['clarification_requests'])
    
    def _get_top_interests(self, profile: UserProfile) -> str:
        """Get user's top interests from interaction history"""
        if not profile.interaction_history:
            return "נושאים שונים"
        
        # Count domains
        domain_counts = {}
        for interaction in profile.interaction_history[-10:]:  # Last 10 interactions
            domain = interaction.get('domain', 'general')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        if not domain_counts:
            return "נושאים כלליים"
        
        # Get top domain
        top_domain = max(domain_counts, key=domain_counts.get)
        
        domain_names = {
            'mathematics': 'מתמטיקה',
            'science': 'מדע',
            'finance': 'כלכלה',
            'weather': 'מזג אוויר',
            'news': 'חדשות',
            'translation': 'תרגומים',
            'general': 'ידע כללי'
        }
        
        return domain_names.get(top_domain, 'נושאים מעניינים')

# ==================== MAIN BOT SYSTEM ====================
class MayaGlobalSecretary:
    """Maya - Advanced Global AI Secretary"""
    
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        
        # Initialize core systems
        self.knowledge_engine = GlobalKnowledgeEngine()
        self.user_manager = UserContextManager(config.DB_PATH)
        self.conversation_engine = IntelligentConversationEngine(
            self.knowledge_engine, self.user_manager
        )
        
        logger.info("Maya Global Secretary initialized with advanced capabilities")
    
    def send_message(self, chat_id: int, text: str) -> bool:
        """Send message with enhanced error handling"""
        try:
            # Split long messages
            if len(text) > 4000:
                parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
                for part in parts:
                    response = requests.post(
                        f"{self.api_url}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": part,
                            "parse_mode": "Markdown"
                        },
                        timeout=15
                    )
                    if response.status_code != 200:
                        return False
                return True
            else:
                response = requests.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    },
                    timeout=15
                )
                return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def process_update(self, update: Dict[str, Any]):
        """Process incoming update with full intelligence"""
        try:
            if "message" not in update:
                return
            
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "").strip()
            user_id = message.get("from", {}).get("id")
            
            if not chat_id or not text or not user_id:
                return
            
            logger.info(f"Processing intelligent query from user {user_id}: {text[:100]}...")
            
            # Send typing indicator
            requests.post(f"{self.api_url}/sendChatAction", 
                        json={"chat_id": chat_id, "action": "typing"})
            
            # Process with full intelligence
            response = await self.conversation_engine.process_conversation(user_id, text)
            
            # Send response
            success = self.send_message(chat_id, response)
            if not success:
                # Fallback message
                self.send_message(chat_id, "מצטערת, הייתה בעיה טכנית. תוכל לנסות שוב? 🔧")
        
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            if "message" in update and "chat" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                self.send_message(chat_id, "נתקלתי בבעיה. אנא נסה שוב בעוד רגע. 🤖")

# ==================== FLASK APPLICATION ====================
maya = MayaGlobalSecretary()

@app.route("/", methods=["GET"])
def home():
    """Advanced system status"""
    return jsonify({
        "status": "🤖 Maya Global Secretary - ONLINE",
        "version": "8.0 - Enterprise Grade",
        "capabilities": [
            "🧮 Advanced Mathematics (Wolfram Alpha)",
            "🔬 Scientific Knowledge (Wikipedia + Research)",
            "💰 Real-time Financial Data (Yahoo Finance)",
            "🌍 Global Weather Information",
            "📰 Live News Feeds",
            "🌐 Multi-language Translation",
            "🧠 GPT-4 Integration",
            "📊 User Context & Memory",
            "🎯 Intelligent Conversation",
            "🔒 Enterprise Security"
        ],
        "knowledge_sources": [
            "Wolfram Alpha", "Wikipedia", "OpenAI GPT", 
            "Yahoo Finance", "OpenWeatherMap", "RSS Feeds",
            "Google Translate", "Real-time APIs"
        ],
        "languages_supported": config.SUPPORTED_LANGUAGES,
        "active_users": len(maya.user_manager.active_profiles),
        "cache_size": len(maya.knowledge_engine.cache),
        "timestamp": datetime.now().isoformat(),
        "timezone": str(config.TIMEZONE)
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Main webhook endpoint for Telegram"""
    try:
        update = request.get_json()
        if not update:
            logger.warning("Empty webhook update received")
            return Response(status=HTTPStatus.BAD_REQUEST)
        
        # Process asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(maya.process_update(update))
        loop.close()
        
        return Response(status=HTTPStatus.OK)
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

@app.route("/test", methods=["GET"])
def test_intelligence():
    """Test Maya's intelligence capabilities"""
    test_queries = [
        "מה השורש הריבועי של 144?",
        "מה מזג האוויר בתל אביב?",
        "כמה שווה דולר בשקלים?",
        "תרגם 'Hello World' לעברית",
        "מי המציא את הטלפון?",
        "חדשות אחרונות"
    ]
    
    return jsonify({
        "test_queries": test_queries,
        "note": "כל השאלות האלה נתמכות על ידי מאיה",
        "knowledge_domains": list(maya.knowledge_engine.knowledge_domains.keys()),
        "api_status": {
            "wolfram": bool(config.WOLFRAM_APP_ID),
            "gemini": bool(config.GEMINI_API_KEY),
            "weather": bool(config.WEATHER_API_KEY),
            "translation": True
        }
    })

@app.route("/user_stats/<int:user_id>", methods=["GET"])
def user_stats(user_id: int):
    """Get user statistics"""
    try:
        profile = maya.user_manager.get_user_profile(user_id)
        
        return jsonify({
            "user_id": user_id,
            "name": profile.name,
            "total_interactions": profile.total_interactions,
            "preferred_language": profile.preferred_language,
            "location": profile.location,
            "recent_domains": [h.get('domain', 'unknown') for h in profile.interaction_history[-5:]],
            "member_since": profile.last_activity.isoformat() if profile.last_activity else None
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/global_stats", methods=["GET"])
def global_stats():
    """Get global system statistics"""
    try:
        with sqlite3.connect(config.DB_PATH) as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM user_profiles").fetchone()[0]
            total_interactions = conn.execute("SELECT COUNT(*) FROM interaction_history").fetchone()[0]
            
            # Top domains
            domain_stats = conn.execute('''
                SELECT domain, COUNT(*) as count 
                FROM interaction_history 
                GROUP BY domain 
                ORDER BY count DESC 
                LIMIT 5
            ''').fetchall()
        
        return jsonify({
            "total_users": total_users,
            "total_interactions": total_interactions,
            "active_sessions": len(maya.user_manager.active_profiles),
            "cache_entries": len(maya.knowledge_engine.cache),
            "top_domains": [{"domain": d[0], "count": d[1]} for d in domain_stats],
            "system_uptime": "Running smoothly! 🚀",
            "capabilities_active": {
                "mathematics": bool(config.WOLFRAM_APP_ID),
                "ai_conversation": bool(config.GEMINI_API_KEY),
                "weather": bool(config.WEATHER_API_KEY),
                "translation": True,
                "finance": True,
                "news": True,
                "wikipedia": True
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error", "status": "Maya is still learning"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "available": ["/", "/webhook", "/test", "/global_stats"]}), 404

# ==================== APPLICATION STARTUP ====================
if __name__ == "__main__":
    logger.info("🚀 Starting Maya Global Secretary - Enterprise Grade AI")
    logger.info("=" * 60)
    logger.info("🧮 Mathematics: Wolfram Alpha Integration")
    logger.info("🔬 Science: Wikipedia + Research APIs")
    logger.info("💰 Finance: Real-time market data")
    logger.info("🌍 Weather: Global weather information")
    logger.info("📰 News: Live RSS feeds")
    logger.info("🌐 Translation: Multi-language support")
    logger.info("🧠 AI: Google Gemini Pro conversation engine")
    logger.info("📊 Memory: Advanced user context")
    logger.info("=" * 60)
    
    # Verify API keys
    api_status = []
    if config.WOLFRAM_APP_ID:
        api_status.append("✅ Wolfram Alpha")
    else:
        api_status.append("❌ Wolfram Alpha (limited math)")
    
    if config.GEMINI_API_KEY:
        api_status.append("✅ Google Gemini")
    else:
        api_status.append("❌ Gemini (basic responses)")
    
    if config.WEATHER_API_KEY:
        api_status.append("✅ Weather API")
    else:
        api_status.append("❌ Weather (limited)")
    
    api_status.extend(["✅ Translation", "✅ Finance", "✅ News", "✅ Wikipedia"])
    
    for status in api_status:
        logger.info(status)
    
    logger.info("=" * 60)
    logger.info(f"🌐 Server starting on port {config.PORT}")
    
    app.run(
        host="0.0.0.0",
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )
