import os

from dotenv import load_dotenv

ENV_FILE = "/app/.env"

load_dotenv(
    dotenv_path=ENV_FILE
)

TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    ""
).strip()

ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "0"
    ).strip()
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()

print("CONFIG LOADED")
print(f"TOKEN EXISTS: {bool(TELEGRAM_TOKEN)}")
print(f"ADMIN ID: {ADMIN_ID}")
print(f"GEMINI EXISTS: {bool(GEMINI_API_KEY)}")
