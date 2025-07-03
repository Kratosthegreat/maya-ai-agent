import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///maya.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "your-fernet-key")
    WEBHOOK_URL = os.getenv("https://maya-bot.onrender.com/webhook", "")
    PORT = int(os.getenv("PORT", 10000))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "30"))

config = Config()
