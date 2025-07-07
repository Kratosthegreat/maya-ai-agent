import os
from dotenv import load_dotenv
import secrets

load_dotenv()

class Config:
"""Configuration class for Maya Bot"""

```
# === TELEGRAM SETTINGS ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# === AI SETTINGS ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# === DATABASE SETTINGS ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///maya.db")

# === SECURITY SETTINGS ===
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", secrets.token_urlsafe(32))

# === APP SETTINGS ===
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PORT = int(os.getenv("PORT", 5000))

# === RATE LIMITING ===
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "30"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

# === EXTERNAL SERVICES ===
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

@classmethod
def validate(cls):
    """Validate required configuration"""
    required_vars = [
        ("TELEGRAM_TOKEN", cls.TELEGRAM_TOKEN),
        ("GEMINI_API_KEY", cls.GEMINI_API_KEY),
    ]
    
    missing = []
    for var_name, var_value in required_vars:
        if not var_value:
            missing.append(var_name)
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    print("✅ Configuration validated successfully")
    return True
```

# Create global config instance

config = Config()

# Validate configuration on import

if **name** != “**main**”:
try:
config.validate()
except ValueError as e:
print(f”❌ Configuration error: {e}”)
print(“Please set the required environment variables in .env file or Render dashboard”)
