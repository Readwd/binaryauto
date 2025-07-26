#!/usr/bin/env python3
"""
Installation Test Script for QXBroker Auto Trading Bot
Verifies that all dependencies are properly installed
"""
import sys
import importlib
from colorama import init, Fore, Style

# Initialize colorama
init()

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name} - {str(e)}")
        return False

def main():
    """Main test function"""
    print(Fore.CYAN + "🤖 QXBroker Auto Trading Bot - Installation Test" + Style.RESET_ALL)
    print("=" * 60)
    
    # Required dependencies
    dependencies = [
        ("quotexpy", "quotexpy (QXBroker API)"),
        ("telethon", "telethon (Telegram client)"),
        ("telegram", "python-telegram-bot"),
        ("websocket", "websocket-client"),
        ("requests", "requests"),
        ("dotenv", "python-dotenv"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("colorama", "colorama"),
        ("termcolor", "termcolor"),
        ("schedule", "schedule"),
        ("pytz", "pytz"),
        ("cryptography", "cryptography"),
        ("aiofiles", "aiofiles"),
        ("websockets", "websockets"),
        ("aiohttp", "aiohttp"),
        ("pydantic", "pydantic"),
        ("sqlalchemy", "sqlalchemy"),
        ("alembic", "alembic")
    ]
    
    print("📦 Testing Dependencies:")
    print("-" * 30)
    
    success_count = 0
    total_count = len(dependencies)
    
    for module, package in dependencies:
        if test_import(module, package):
            success_count += 1
    
    print("\n" + "=" * 60)
    
    # Test custom modules
    print("🔧 Testing Custom Modules:")
    print("-" * 30)
    
    custom_modules = [
        ("config", "Configuration module"),
        ("core", "Core models"),
        ("brokers", "Broker clients"),
        ("telegram_integration", "Telegram integration"),
        ("trading", "Trading engine")
    ]
    
    custom_success = 0
    custom_total = len(custom_modules)
    
    for module, description in custom_modules:
        if test_import(module, description):
            custom_success += 1
    
    print("\n" + "=" * 60)
    
    # Summary
    print("📊 Test Summary:")
    print("-" * 15)
    
    dependency_percentage = (success_count / total_count) * 100
    custom_percentage = (custom_success / custom_total) * 100
    
    print(f"Dependencies: {success_count}/{total_count} ({dependency_percentage:.1f}%)")
    print(f"Custom modules: {custom_success}/{custom_total} ({custom_percentage:.1f}%)")
    
    if success_count == total_count and custom_success == custom_total:
        print(Fore.GREEN + "\n✅ All tests passed! Installation is complete." + Style.RESET_ALL)
        print("🚀 You can now run the bot with: python main.py")
        return 0
    else:
        print(Fore.RED + "\n❌ Some tests failed. Please install missing dependencies." + Style.RESET_ALL)
        print("📋 Install missing packages with: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())