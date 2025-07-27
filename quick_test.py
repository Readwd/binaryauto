#!/usr/bin/env python3
"""
Quick test for basic imports
"""
import sys

def test_import(module_name, description):
    try:
        __import__(module_name)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        print(f"❌ {description} - {str(e)}")
        return False

def main():
    print(f"🐍 Python version: {sys.version}")
    print("=" * 50)
    
    tests = [
        ("requests", "HTTP requests"),
        ("dotenv", "Environment variables"),
        ("colorama", "Terminal colors"),
        ("pydantic", "Data validation"),
        ("aiohttp", "Async HTTP"),
        ("telethon", "Telegram client"),
        ("quotexpy", "QXBroker API")
    ]
    
    success_count = 0
    for module, desc in tests:
        if test_import(module, desc):
            success_count += 1
    
    print("=" * 50)
    print(f"📊 Results: {success_count}/{len(tests)} imports successful")
    
    if success_count >= len(tests) - 1:  # Allow 1 failure
        print("✅ Installation looks good!")
        return 0
    else:
        print("⚠️ Some issues found")
        return 1

if __name__ == "__main__":
    sys.exit(main())