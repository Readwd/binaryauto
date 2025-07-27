#!/usr/bin/env python3
"""
QXBroker Auto Trading Bot - Python 3.13+ Installation Script
For Python 3.13 and newer versions that quotexpy doesn't officially support
"""
import os
import sys
import subprocess
import platform

def check_python_version():
    """Check and display Python version"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    if version.major == 3 and version.minor >= 13:
        print("⚠️  Python 3.13+ detected - quotexpy may not be officially compatible")
        print("✅ Using compatibility mode with alternative installation methods")
        return "python313"
    
    print("✅ Python version is compatible")
    return "compatible"

def run_command(command, description, ignore_errors=False):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            print(f"⚠️ {description} failed (continuing anyway)")
            if e.stderr:
                print(f"Error: {e.stderr}")
            return False
        else:
            print(f"❌ {description} failed")
            if e.stdout:
                print(f"Output: {e.stdout}")
            if e.stderr:
                print(f"Error: {e.stderr}")
            return False

def install_python313_packages():
    """Install packages compatible with Python 3.13+"""
    
    # Upgrade pip first
    print("📦 Upgrading pip and essential tools...")
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    run_command("pip install --upgrade setuptools wheel", "Upgrading setuptools and wheel")
    
    # Core packages that should work with Python 3.13
    core_packages = [
        "requests>=2.31.0",
        "python-dotenv>=1.0.0", 
        "colorama>=0.4.6",
        "termcolor>=2.3.0",
        "pytz>=2023.3"
    ]
    
    print("📦 Installing core packages...")
    for package in core_packages:
        run_command(f"pip install '{package}'", f"Installing {package}")
    
    # Pydantic v2 (compatible with Python 3.13)
    print("📦 Installing Pydantic v2...")
    run_command("pip install 'pydantic>=2.0.0'", "Installing Pydantic v2")
    
    # Async packages
    async_packages = [
        "aiohttp>=3.9.0",
        "websockets>=12.0",
        "aiofiles>=23.2.0"
    ]
    
    print("📦 Installing async packages...")
    for package in async_packages:
        run_command(f"pip install '{package}'", f"Installing {package}")
    
    # Telegram (should work with Python 3.13)
    print("📦 Installing Telegram client...")
    run_command("pip install 'telethon>=1.34.0'", "Installing Telethon")
    
    # Try to install quotexpy - multiple approaches
    print("📦 Installing QuotexPy (trying multiple methods)...")
    quotex_installed = False
    
    # Method 1: Try latest version (might work despite version restriction)
    print("🔄 Trying latest quotexpy version...")
    if run_command("pip install quotexpy --no-deps", "Installing quotexpy (no deps)", ignore_errors=True):
        # Install dependencies separately
        deps = ["requests", "websocket-client", "python-socketio[client]"]
        for dep in deps:
            run_command(f"pip install '{dep}'", f"Installing {dep}", ignore_errors=True)
        quotex_installed = True
    
    # Method 2: Try from GitHub
    if not quotex_installed:
        print("🔄 Trying quotexpy from GitHub...")
        github_urls = [
            "git+https://github.com/SantiiRepair/quotexpy.git",
            "git+https://github.com/cleitonleonel/pyquotex.git"
        ]
        
        for url in github_urls:
            if run_command(f"pip install {url}", f"Installing from {url}", ignore_errors=True):
                quotex_installed = True
                break
    
    # Method 3: Try specific older version with --force-reinstall
    if not quotex_installed:
        print("🔄 Trying to force install older quotexpy version...")
        if run_command("pip install quotexpy==1.0.38 --force-reinstall --no-deps", "Force installing quotexpy 1.0.38", ignore_errors=True):
            quotex_installed = True
    
    if quotex_installed:
        print("✅ QuotexPy installed successfully")
    else:
        print("⚠️ Could not install quotexpy automatically")
        print("📝 Manual installation options:")
        print("   1. pip install quotexpy --no-deps --force-reinstall")
        print("   2. pip install git+https://github.com/SantiiRepair/quotexpy.git")
        print("   3. Download and install manually from GitHub")
    
    # Optional packages
    optional_packages = [
        "pandas>=2.1.0",
        "numpy>=1.25.0", 
        "sqlalchemy>=2.0.0",
        "cryptography>=41.0.0"
    ]
    
    print("📦 Installing optional packages...")
    for package in optional_packages:
        run_command(f"pip install '{package}'", f"Installing {package}", ignore_errors=True)

def create_project_structure():
    """Create the project directory structure"""
    print("📁 Creating project structure...")
    
    directories = [
        "config",
        "core", 
        "brokers",
        "telegram_integration",
        "trading",
        "utils"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Create __init__.py files
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f'"""{directory.title()} module for QXBroker Trading Bot"""\n')
    
    print("✅ Project structure created")

def create_env_file():
    """Create .env file from example"""
    if os.path.exists(".env.example") and not os.path.exists(".env"):
        print("📝 Creating .env file from template...")
        try:
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ .env file created. Please edit it with your credentials.")
        except Exception as e:
            print(f"⚠️ Could not create .env file: {e}")
    elif os.path.exists(".env"):
        print("✅ .env file already exists")
    else:
        print("⚠️ .env.example not found, creating basic .env file...")
        basic_env = """# QXBroker Configuration
QXBROKER_EMAIL=your_email@example.com
QXBROKER_PASSWORD=your_password
QXBROKER_MODE=PRACTICE
QXBROKER_HOST=qxbroker.com

# Telegram Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE_NUMBER=+1234567890
TELEGRAM_CHAT_ID=your_chat_id

# Trading Configuration
DEFAULT_TRADE_AMOUNT=10.0
MARTINGALE_ENABLED=true
MAX_DAILY_LOSS=100.0
"""
        try:
            with open(".env", "w") as f:
                f.write(basic_env)
            print("✅ Basic .env file created")
        except Exception as e:
            print(f"❌ Could not create .env file: {e}")

def test_installation():
    """Test if key packages are working"""
    print("🧪 Testing installation...")
    
    test_imports = [
        ("requests", "requests"),
        ("dotenv", "python-dotenv"),
        ("colorama", "colorama"),
        ("pydantic", "pydantic"),
        ("telethon", "telethon"),
        ("quotexpy", "quotexpy")
    ]
    
    success_count = 0
    for module, package in test_imports:
        try:
            if module == "quotexpy":
                # Try multiple import paths for quotexpy
                try:
                    import quotexpy
                    print(f"✅ {package}")
                    success_count += 1
                except ImportError:
                    try:
                        import quotex_api
                        print(f"✅ {package} (via quotex_api)")
                        success_count += 1
                    except ImportError:
                        print(f"❌ {package} - will need manual installation")
            else:
                __import__(module)
                print(f"✅ {package}")
                success_count += 1
        except ImportError as e:
            print(f"❌ {package} - {str(e)}")
    
    print(f"\n📊 Test Results: {success_count}/{len(test_imports)} packages working")
    
    if success_count >= len(test_imports) - 1:  # Allow quotexpy to fail
        print("✅ Installation looks good!")
        return True
    else:
        print("⚠️ Some packages are missing, but the bot may still work")
        return False

def create_compatibility_fixes():
    """Create compatibility fixes for Python 3.13"""
    print("🔧 Creating Python 3.13 compatibility fixes...")
    
    # Create a compatibility wrapper for quotexpy
    compat_code = '''"""
Compatibility wrapper for quotexpy with Python 3.13+
"""
import sys
import warnings

# Suppress version warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from quotexpy import Quotex
    QUOTEXPY_AVAILABLE = True
    print("✅ quotexpy imported successfully")
except ImportError as e:
    print(f"⚠️ quotexpy import failed: {e}")
    try:
        # Try alternative import
        from quotex_api.stable_api import Quotex
        QUOTEXPY_AVAILABLE = True
        print("✅ quotex_api imported as fallback")
    except ImportError:
        print("❌ No quotex library available - using mock mode")
        
        # Create a mock Quotex class for testing
        class MockQuotex:
            def __init__(self, *args, **kwargs):
                self.connected = False
                self.balance = 1000.0
                
            def connect(self):
                print("🔄 Mock connection (quotexpy not available)")
                self.connected = True
                return True, "Mock connection successful"
                
            def disconnect(self):
                self.connected = False
                
            def get_balance(self):
                return self.balance
                
            def buy(self, asset, amount, direction, duration):
                print(f"🔄 Mock trade: {asset} {direction} ${amount} for {duration}s")
                return f"mock_trade_{hash(f'{asset}{amount}{direction}')}"
                
            def check_win(self, trade_id):
                # Simulate 60% win rate
                import random
                return amount * 0.8 if random.random() < 0.6 else 0
                
            def check_asset_open(self, asset):
                return True
                
            def get_payment(self):
                return {"EURUSD_otc": {"payment": 0.8}}
        
        Quotex = MockQuotex
        QUOTEXPY_AVAILABLE = False

__all__ = ['Quotex', 'QUOTEXPY_AVAILABLE']
'''
    
    try:
        with open("quotex_compat.py", "w") as f:
            f.write(compat_code)
        print("✅ Compatibility wrapper created")
    except Exception as e:
        print(f"⚠️ Could not create compatibility wrapper: {e}")

def main():
    """Main installation function"""
    print("🤖 QXBroker Auto Trading Bot - Python 3.13+ Installation")
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 70)
    
    # Check Python version
    python_check = check_python_version()
    if python_check == False:
        return 1
    
    print("\n🚀 Starting installation for Python 3.13+...")
    
    # Create project structure
    create_project_structure()
    
    # Install packages
    install_python313_packages()
    
    # Create compatibility fixes
    create_compatibility_fixes()
    
    # Create .env file
    create_env_file()
    
    # Test installation
    test_installation()
    
    print("\n" + "=" * 70)
    print("✅ Python 3.13+ installation completed!")
    
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your credentials")
    print("2. Make sure all Python files are in their correct folders:")
    print("   - config/settings.py")
    print("   - core/models.py") 
    print("   - brokers/qxbroker_client.py")
    print("   - telegram_integration/client.py")
    print("   - telegram_integration/signal_parser.py")
    print("   - trading/risk_manager.py")
    print("   - trading/trade_executor.py")
    print("   - main.py")
    print("3. Run: python test_installation.py")
    print("4. Run: python main.py")
    
    print("\n⚠️  Important Notes for Python 3.13:")
    print("- quotexpy may not be officially supported")
    print("- The bot includes compatibility workarounds")
    print("- Use PRACTICE mode first to test everything")
    print("- If quotexpy fails, you may need to:")
    print("  * Use an older Python version (3.10-3.12)")
    print("  * Or wait for quotexpy to support Python 3.13")
    
    print("\n🚀 Happy trading!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\nPress Enter to exit...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Installation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        input("Press Enter to exit...")
        sys.exit(1)