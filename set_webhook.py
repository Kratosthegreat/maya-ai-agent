import requests
TOKEN = "7876544988:AAGE12C8OmAyqT9pY9voqn_3IcYLvHBNMio"
WEBHOOK_URL = "https://maya-bot.onrender.com/webhook"
requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
