# config.py
import os

# --- IMPORTANT: Replace these with your actual values or environment variables ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://YOUR_RENDER_APP_NAME.onrender.com/webhook")
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "a_very_secret_key_for_flask") # Used by Flask

# --- General Configuration ---
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development") # Set to "production" on Render
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t") # False for production
PORT = int(os.environ.get("PORT", 10000)) # Render provides this
MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", 20)) # Your custom rate limit
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-pro") # Or "gemini-1.5-pro-latest"
