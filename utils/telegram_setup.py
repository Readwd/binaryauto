#!/usr/bin/env python3
"""
Telegram Setup Utility for QXBroker Auto Trading Bot
Helps users authenticate with Telegram and get session information
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
except ImportError:
    print("❌ Error: telethon library not installed")
    print("Please install it with: pip install telethon")
    sys.exit(1)

from config import settings

async def setup_telegram():
    """Setup Telegram authentication"""
    print("🤖 QXBroker Trading Bot - Telegram Setup")
    print("=" * 50)
    
    # Check if API credentials are configured
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        print("❌ Telegram API credentials not configured!")
        print("\nTo get your API credentials:")
        print("1. Go to https://my.telegram.org/")
        print("2. Log in with your phone number")
        print("3. Go to 'API Development Tools'")
        print("4. Create a new application")
        print("5. Copy the API ID and API Hash to your .env file")
        print("\nExample .env entries:")
        print("TELEGRAM_API_ID=1234567")
        print("TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890")
        return False
    
    print(f"✅ API ID: {settings.telegram_api_id}")
    print(f"✅ API Hash: {settings.telegram_api_hash[:8]}...")
    
    if not settings.telegram_phone_number:
        phone = input("\n📱 Enter your phone number (with country code, e.g., +1234567890): ")
        if not phone.startswith('+'):
            phone = '+' + phone
    else:
        phone = settings.telegram_phone_number
        print(f"📱 Using phone number: {phone}")
    
    print(f"\n🔄 Connecting to Telegram...")
    
    # Create client
    client = TelegramClient('trading_bot_session', settings.telegram_api_id, settings.telegram_api_hash)
    
    try:
        await client.connect()
        
        # Check if already authorized
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ Already authenticated as {me.first_name} (@{me.username})")
            
            # List recent chats
            print("\n📋 Recent chats:")
            print("-" * 30)
            
            async for dialog in client.iter_dialogs(limit=10):
                chat_type = "Channel" if dialog.is_channel else "Group" if dialog.is_group else "User"
                print(f"ID: {dialog.id} | {chat_type}: {dialog.name}")
            
            print("\n💡 To monitor a specific chat, add its ID to your .env file:")
            print("TELEGRAM_CHAT_ID=your_chat_id")
            
        else:
            print("🔐 Not authenticated. Starting authentication process...")
            
            # Send code request
            await client.send_code_request(phone)
            print(f"📨 Verification code sent to {phone}")
            
            # Get verification code
            code = input("🔢 Enter the verification code: ")
            
            try:
                await client.sign_in(phone, code)
                
            except SessionPasswordNeededError:
                # Two-factor authentication enabled
                password = input("🔒 Two-factor authentication enabled. Enter your password: ")
                await client.sign_in(password=password)
            
            except PhoneCodeInvalidError:
                print("❌ Invalid verification code!")
                return False
            
            # Get user info
            me = await client.get_me()
            print(f"✅ Successfully authenticated as {me.first_name} (@{me.username})")
            
            # List recent chats
            print("\n📋 Recent chats:")
            print("-" * 30)
            
            async for dialog in client.iter_dialogs(limit=10):
                chat_type = "Channel" if dialog.is_channel else "Group" if dialog.is_group else "User"
                print(f"ID: {dialog.id} | {chat_type}: {dialog.name}")
            
            print("\n💡 To monitor a specific chat, add its ID to your .env file:")
            print("TELEGRAM_CHAT_ID=your_chat_id")
        
        print("\n✅ Telegram setup completed successfully!")
        print("🔄 You can now run the trading bot with: python main.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        return False
        
    finally:
        await client.disconnect()

async def test_signal_parsing():
    """Test signal parsing with sample messages"""
    print("\n🧪 Testing Signal Parsing")
    print("=" * 30)
    
    # Import signal parser
    from telegram_integration import TelegramSignalParser
    
    parser = TelegramSignalParser()
    
    # Test messages
    test_messages = [
        "EURUSD CALL $10 5M",
        "GBPUSD PUT 15 3M",
        "AUDUSD 📈 20 minutes",
        "USDJPY DOWN $25 10M",
        "Asset: EURGBP\nDirection: CALL\nAmount: $30\nDuration: 5M",
        "USDCAD UP 5 minutes confidence 85%",
        "Invalid message without signal",
        "NZDUSD CALL at 14:30 for 5 minutes"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: '{message}'")
        
        signal = parser.parse_message(message)
        if signal:
            is_valid = parser.validate_signal(signal)
            status = "✅ Valid" if is_valid else "⚠️ Invalid"
            print(f"   {status} - {signal.asset} {signal.direction.value.upper()} ${signal.amount} {signal.duration}s")
            if signal.confidence:
                print(f"   Confidence: {signal.confidence}%")
        else:
            print("   ❌ No signal detected")
    
    print(f"\n📊 Parser Statistics:")
    stats = parser.get_signal_statistics()
    print(f"   Patterns: {stats['patterns_count']}")
    print(f"   Allowed assets: {', '.join(stats['allowed_assets'])}")
    print(f"   Min confidence: {stats['min_confidence']}%")

async def get_chat_info():
    """Get information about a specific chat"""
    print("\n🔍 Get Chat Information")
    print("=" * 30)
    
    chat_input = input("Enter chat ID or username: ")
    if not chat_input:
        print("❌ No chat specified")
        return
    
    client = TelegramClient('trading_bot_session', settings.telegram_api_id, settings.telegram_api_hash)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ Not authenticated. Please run setup first.")
            return
        
        # Get chat entity
        try:
            chat = await client.get_entity(chat_input)
            
            print(f"✅ Chat found:")
            print(f"   ID: {chat.id}")
            print(f"   Title: {getattr(chat, 'title', 'N/A')}")
            print(f"   Username: {getattr(chat, 'username', 'N/A')}")
            print(f"   Type: {'Channel' if getattr(chat, 'broadcast', False) else 'Group' if hasattr(chat, 'participants_count') else 'User'}")
            
            if hasattr(chat, 'participants_count'):
                print(f"   Members: {chat.participants_count}")
            
            # Get recent messages
            print(f"\n📨 Recent messages:")
            print("-" * 20)
            
            count = 0
            async for message in client.iter_messages(chat, limit=5):
                if message.text:
                    count += 1
                    sender = message.sender.username if message.sender else "Unknown"
                    text = message.text[:50] + "..." if len(message.text) > 50 else message.text
                    print(f"   {count}. @{sender}: {text}")
            
            if count == 0:
                print("   No recent text messages found")
                
        except Exception as e:
            print(f"❌ Error getting chat info: {str(e)}")
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        
    finally:
        await client.disconnect()

async def main():
    """Main menu"""
    while True:
        print("\n🤖 QXBroker Trading Bot - Telegram Setup")
        print("=" * 50)
        print("1. Setup Telegram Authentication")
        print("2. Test Signal Parsing")
        print("3. Get Chat Information")
        print("4. Exit")
        
        choice = input("\nSelect an option (1-4): ").strip()
        
        if choice == '1':
            await setup_telegram()
        elif choice == '2':
            await test_signal_parsing()
        elif choice == '3':
            await get_chat_info()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)