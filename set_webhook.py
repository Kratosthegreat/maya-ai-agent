import requests
from config import config
import sys

def set_webhook():
    """Set webhook for the Telegram bot"""
    
    if not config.TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_TOKEN not found in environment variables")
        return False
    
    if not config.WEBHOOK_URL:
        print("❌ Error: WEBHOOK_URL not found in environment variables")
        return False
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook"
    data = {
        "url": config.WEBHOOK_URL,
        "allowed_updates": ["message", "callback_query"]
    }
    
    try:
        print(f"🔗 Setting webhook to: {config.WEBHOOK_URL}")
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook set successfully!")
            print(f"Description: {result.get('description', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to set webhook: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return False

def get_webhook_info():
    """Get current webhook information"""
    
    if not config.TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_TOKEN not found")
        return False
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            webhook_info = result.get("result", {})
            print("📋 Current webhook info:")
            print(f"  URL: {webhook_info.get('url', 'Not set')}")
            print(f"  Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
            print(f"  Pending update count: {webhook_info.get('pending_update_count', 0)}")
            print(f"  Last error date: {webhook_info.get('last_error_date', 'None')}")
            print(f"  Last error message: {webhook_info.get('last_error_message', 'None')}")
            print(f"  Max connections: {webhook_info.get('max_connections', 'N/A')}")
            print(f"  Allowed updates: {webhook_info.get('allowed_updates', 'All')}")
            return True
        else:
            print(f"❌ Failed to get webhook info: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting webhook info: {e}")
        return False

def delete_webhook():
    """Delete current webhook"""
    
    if not config.TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_TOKEN not found")
        return False
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/deleteWebhook"
    
    try:
        response = requests.post(url, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook deleted successfully!")
            return True
        else:
            print(f"❌ Failed to delete webhook: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting webhook: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Maya Bot Webhook Manager")
    print("=" * 40)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "set":
            set_webhook()
        elif command == "info":
            get_webhook_info
