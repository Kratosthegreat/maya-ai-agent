#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maya AI Bot Startup Script
Starts the bot with proper error handling and monitoring
"""

import asyncio
import os
import sys
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

def check_environment():
    """Check that required environment variables are set"""
    print("🔍 Checking environment configuration...")
    
    required_vars = ['TELEGRAM_BOT_TOKEN', 'GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease ensure your .env file contains:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        print("\nSee .env.example for reference.")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Maya AI Bot...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Import and start the bot
    try:
        from main import main as start_bot
        print("✅ Modules loaded successfully")
        print("🤖 Starting Maya AI Bot...")
        
        # Start the bot
        start_bot()
        
    except KeyboardInterrupt:
        print("\n👋 Maya AI Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()