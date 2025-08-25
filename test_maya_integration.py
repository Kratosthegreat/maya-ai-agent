#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Maya AI Bot
Tests the integration of IntelligentMayaAgent with fallbacks
"""

import asyncio
import os
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test environment configuration"""
    print("🔍 Testing environment configuration...")
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    print(f"BOT_TOKEN: {'✅ Set' if bot_token else '❌ Missing'}")
    print(f"GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Missing'}")
    
    return bot_token and gemini_key

def test_imports():
    """Test all necessary imports"""
    print("\n🔍 Testing imports...")
    
    try:
        from main import MayaBot, MayaAI
        print("✅ Main classes imported successfully")
        
        from intelligent_maya import IntelligentMayaAgent, init_intelligent_maya
        print("✅ Intelligent Maya classes imported successfully")
        
        import google.generativeai as genai
        print("✅ Google Generative AI imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_bot_initialization():
    """Test bot initialization"""
    print("\n🔍 Testing bot initialization...")
    
    # Mock telegram token to avoid API calls
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
    
    try:
        from main import MayaBot
        bot = MayaBot()
        
        print(f"✅ MayaBot initialized")
        print(f"   Intelligent agent: {'✅' if bot.intelligent_agent else '❌'}")
        print(f"   Traditional AI: {'✅' if bot.ai else '❌'}")
        print(f"   Database: {'✅' if bot.db else '❌'}")
        
        return True
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return False

@pytest.mark.asyncio
async def test_simple_gemini():
    """Test simple Gemini API call"""
    print("\n🔍 Testing simple Gemini API call...")
    
    try:
        import google.generativeai as genai
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            print("❌ No Gemini API key")
            return False
        
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content("שלום! תן לי תשובה קצרה בעברית")
        if response.text:
            print(f"✅ Gemini API working: {response.text[:50]}...")
            return True
        else:
            print("❌ Empty response from Gemini")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

@pytest.mark.asyncio
async def test_traditional_ai():
    """Test traditional AI system"""
    print("\n🔍 Testing traditional AI system...")
    
    try:
        # Mock telegram token to avoid API calls
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        
        from main import MayaAI
        ai = MayaAI()
        
        # Test a simple message
        test_user_id = 12345
        test_message = "שלום מאיה"
        
        response, keyboard, task_id = await ai.generate_response(
            user_id=test_user_id,
            message=test_message
        )
        
        print(f"✅ Traditional AI response: {response[:50]}...")
        print(f"   Keyboard: {'✅' if keyboard else '❌'}")
        print(f"   Task ID: {task_id if task_id else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Traditional AI test failed: {e}")
        return False

@pytest.mark.asyncio
async def test_message_handling():
    """Test complete message handling flow"""
    print("\n🔍 Testing complete message handling...")
    
    try:
        # Mock telegram token to avoid API calls
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        
        from main import MayaBot
        bot = MayaBot()
        
        # Create mock update object
        class MockUser:
            def __init__(self):
                self.id = 12345
                self.username = "test_user"
                self.first_name = "Test"
        
        class MockMessage:
            def __init__(self):
                self.text = "שלום מאיה! איך הולך?"
        
        class MockUpdate:
            def __init__(self):
                self.effective_user = MockUser()
                self.message = MockMessage()
        
        # Create mock context (we won't actually send messages)
        mock_update = MockUpdate()
        
        # Test the logic without actually sending Telegram messages
        user = mock_update.effective_user
        message = mock_update.message.text
        
        # Register user
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
        bot.db.register_user(user_data)
        
        print("✅ User registration successful")
        
        # Test message processing logic
        if bot.intelligent_agent:
            print("✅ Will use intelligent agent for processing")
        else:
            print("⚠️ Will use traditional AI as fallback")
        
        return True
        
    except Exception as e:
        print(f"❌ Message handling test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Maya AI Bot Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("Bot Initialization", test_bot_initialization),
        ("Simple Gemini API", test_simple_gemini),
        ("Traditional AI", test_traditional_ai),
        ("Message Handling", test_message_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Maya AI Bot is ready!")
    elif passed >= total * 0.75:
        print("⚠️ Most tests passed. Minor issues to resolve.")
    else:
        print("❌ Critical issues detected. Please review errors.")

if __name__ == "__main__":
    asyncio.run(main())