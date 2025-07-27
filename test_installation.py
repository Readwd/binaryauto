#!/usr/bin/env python3
"""
QXBroker Auto Trading Bot - Installation Test Script
Test all components to ensure they're working correctly
"""
import sys
import os
import traceback
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def test_python_version():
    """Test Python version"""
    print_header("Python Version Check")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ required")
        return False

def test_core_imports():
    """Test core package imports"""
    print_header("Core Package Imports")
    
    packages = [
        ("os", "Built-in OS module"),
        ("sys", "Built-in sys module"),
        ("asyncio", "Built-in asyncio module"),
        ("datetime", "Built-in datetime module"),
        ("typing", "Built-in typing module"),
        ("enum", "Built-in enum module"),
        ("uuid", "Built-in uuid module"),
        ("logging", "Built-in logging module"),
        ("re", "Built-in regex module")
    ]
    
    success_count = 0
    for module, description in packages:
        try:
            __import__(module)
            print(f"✅ {description}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {description} - {str(e)}")
    
    print(f"\nCore imports: {success_count}/{len(packages)} successful")
    return success_count == len(packages)

def test_external_packages():
    """Test external package imports"""
    print_header("External Package Imports")
    
    packages = [
        ("requests", "HTTP requests library"),
        ("dotenv", "Environment variables loader"),
        ("colorama", "Terminal colors"),
        ("termcolor", "Terminal text coloring"),
        ("pytz", "Timezone handling"),
        ("pydantic", "Data validation"),
        ("aiohttp", "Async HTTP client"),
        ("websockets", "WebSocket client"),
        ("aiofiles", "Async file operations"),
        ("telethon", "Telegram client"),
        ("quotexpy", "QXBroker API (may fail)")
    ]
    
    success_count = 0
    for module, description in packages:
        try:
            if module == "dotenv":
                from dotenv import load_dotenv
            elif module == "quotexpy":
                try:
                    import quotexpy
                    print(f"✅ {description}")
                    success_count += 1
                    continue
                except ImportError:
                    try:
                        import quotex_api
                        print(f"✅ {description} (via quotex_api)")
                        success_count += 1
                        continue
                    except ImportError:
                        print(f"⚠️ {description} - Not available (expected for Python 3.13+)")
                        continue
            else:
                __import__(module)
            print(f"✅ {description}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {description} - {str(e)}")
    
    print(f"\nExternal packages: {success_count}/{len(packages)} successful")
    return success_count >= len(packages) - 2  # Allow 2 failures

def test_project_structure():
    """Test project directory structure"""
    print_header("Project Structure Check")
    
    required_dirs = [
        "config",
        "core",
        "brokers", 
        "telegram_integration",
        "trading",
        "utils"
    ]
    
    required_files = [
        "config/__init__.py",
        "config/settings.py",
        "core/__init__.py",
        "core/models.py",
        "brokers/__init__.py",
        "brokers/qxbroker_client.py",
        "telegram_integration/__init__.py",
        "telegram_integration/client.py",
        "telegram_integration/signal_parser.py",
        "trading/__init__.py", 
        "trading/risk_manager.py",
        "trading/trade_executor.py",
        "main.py",
        ".env.example"
    ]
    
    # Check directories
    missing_dirs = []
    for directory in required_dirs:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✅ Directory: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            missing_dirs.append(directory)
    
    # Check files
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✅ File: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"\n⚠️ Missing directories: {', '.join(missing_dirs)}")
    if missing_files:
        print(f"\n⚠️ Missing files: {', '.join(missing_files)}")
    
    return len(missing_dirs) == 0 and len(missing_files) == 0

def test_config_loading():
    """Test configuration loading"""
    print_header("Configuration Loading Test")
    
    try:
        # Test if .env file exists
        if os.path.exists('.env'):
            print("✅ .env file found")
        else:
            print("⚠️ .env file not found (using defaults)")
        
        # Test config import
        try:
            from config.settings import settings
            print("✅ Settings imported successfully")
            
            # Test some basic settings
            print(f"✅ QXBroker mode: {settings.qxbroker_mode}")
            print(f"✅ QXBroker host: {settings.qxbroker_host}")
            print(f"✅ Default trade amount: ${settings.default_trade_amount}")
            print(f"✅ Log level: {settings.log_level}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error importing settings: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False

def test_models():
    """Test data models"""
    print_header("Data Models Test")
    
    try:
        from core.models import (
            TradingSignal, Trade, TradeDirection, TradeStatus,
            TradingSession, RiskMetrics, BrokerConnection
        )
        
        # Test TradingSignal creation
        signal = TradingSignal(
            asset="EURUSD",
            direction=TradeDirection.CALL,
            amount=10.0,
            duration=300
        )
        print("✅ TradingSignal model works")
        
        # Test Trade creation
        trade = Trade(
            signal_id=signal.id,
            asset="EURUSD",
            direction=TradeDirection.CALL,
            amount=10.0,
            duration=300
        )
        print("✅ Trade model works")
        
        # Test TradingSession
        session = TradingSession(balance_start=1000.0)
        print(f"✅ TradingSession model works - Win rate: {session.win_rate}%")
        
        # Test RiskMetrics
        risk = RiskMetrics()
        print(f"✅ RiskMetrics model works - Daily P&L: ${risk.daily_pnl}")
        
        # Test BrokerConnection
        connection = BrokerConnection()
        connection.update_connection_status(True)
        print("✅ BrokerConnection model works")
        
        return True
        
    except Exception as e:
        print(f"❌ Models test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_signal_parser():
    """Test signal parser"""
    print_header("Signal Parser Test")
    
    try:
        from telegram_integration.signal_parser import TelegramSignalParser
        
        parser = TelegramSignalParser()
        
        # Test signal parsing
        test_messages = [
            "EURUSD CALL $10 5M",
            "GBPUSD PUT 15 3M",
            "EURUSD 📈 5M",
            "AUDUSD UP 10 minutes"
        ]
        
        parsed_count = 0
        for message in test_messages:
            signal = parser.parse_message(message)
            if signal:
                print(f"✅ Parsed: '{message}' -> {signal.asset} {signal.direction.value} ${signal.amount}")
                parsed_count += 1
            else:
                print(f"❌ Failed to parse: '{message}'")
        
        print(f"\nSignal parser: {parsed_count}/{len(test_messages)} messages parsed")
        return parsed_count > 0
        
    except Exception as e:
        print(f"❌ Signal parser test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_broker_client():
    """Test broker client (without actual connection)"""
    print_header("Broker Client Test")
    
    try:
        from brokers.qxbroker_client import QXBrokerClient
        
        # Just test instantiation
        client = QXBrokerClient()
        print("✅ QXBrokerClient instantiated successfully")
        
        # Test connection status
        print(f"✅ Connection status: {client.is_connected()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Broker client test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_risk_manager():
    """Test risk manager"""
    print_header("Risk Manager Test")
    
    try:
        from trading.risk_manager import RiskManager
        
        risk_manager = RiskManager()
        
        # Start a session
        session = risk_manager.start_session(1000.0)
        print(f"✅ Trading session started: {session.id}")
        
        # Test risk summary
        summary = risk_manager.get_risk_summary()
        print(f"✅ Risk summary generated: {len(summary)} metrics")
        
        # Test recommendations
        recommendations = risk_manager.get_trading_recommendations()
        print(f"✅ Trading recommendations: {len(recommendations)} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk manager test failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🤖 QXBroker Auto Trading Bot - Installation Test")
    print(f"📅 Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Python Version", test_python_version),
        ("Core Imports", test_core_imports),
        ("External Packages", test_external_packages),
        ("Project Structure", test_project_structure),
        ("Configuration", test_config_loading),
        ("Data Models", test_models),
        ("Signal Parser", test_signal_parser),
        ("Broker Client", test_broker_client),
        ("Risk Manager", test_risk_manager)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_header("Test Results Summary")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            print(f"✅ {test_name}")
            passed += 1
        else:
            print(f"❌ {test_name}")
            failed += 1
    
    print(f"\n📊 Overall Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The bot should work correctly.")
        print("\n📋 Next steps:")
        print("1. Edit .env file with your credentials")
        print("2. Run: python main.py")
    elif passed >= len(results) - 2:
        print("\n⚠️ Most tests passed. The bot should work with minor issues.")
        print("\n📋 Next steps:")
        print("1. Check failed tests above")
        print("2. Edit .env file with your credentials")
        print("3. Run: python main.py")
    else:
        print("\n❌ Multiple tests failed. Please fix issues before running the bot.")
        print("\n📋 Troubleshooting:")
        print("1. Make sure all files are in correct directories")
        print("2. Run the installation script again")
        print("3. Check Python version compatibility")
    
    return 0 if passed >= len(results) - 2 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\nPress Enter to exit...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)