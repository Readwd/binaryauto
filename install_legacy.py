#!/usr/bin/env python3
"""
QXBroker Auto Trading Bot - Legacy Installation Script
For Python 3.8, 3.9 and other older versions
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
        print("Please upgrade Python from https://python.org/downloads/")
        return False
    
    if version.major == 3 and version.minor >= 10:
        print("✅ You can use the regular requirements.txt")
        print("Run: pip install -r requirements.txt")
        return "modern"
    
    print("✅ Using legacy compatibility mode")
    return "legacy"

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def install_legacy_packages():
    """Install packages compatible with older Python versions"""
    
    # Essential packages first
    essential_packages = [
        "pip>=21.0",
        "setuptools>=50.0",
        "wheel"
    ]
    
    print("📦 Installing essential packages...")
    for package in essential_packages:
        run_command(f"pip install --upgrade {package}", f"Installing {package}")
    
    # Core packages
    core_packages = [
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
        "colorama>=0.4.4",
        "termcolor>=1.1.0",
        "pytz>=2021.1"
    ]
    
    print("📦 Installing core packages...")
    for package in core_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            print(f"⚠️ Failed to install {package}, continuing...")
    
    # Pydantic v1 (important for compatibility)
    print("📦 Installing Pydantic v1...")
    pydantic_versions = ["pydantic>=1.10.0,<2.0.0", "pydantic>=1.8.0,<2.0.0", "pydantic==1.10.12"]
    for version in pydantic_versions:
        if run_command(f"pip install '{version}'", f"Installing {version}"):
            break
    
    # Async packages
    async_packages = [
        "aiohttp>=3.7.0,<4.0.0",
        "websockets>=10.0,<11.0",
        "aiofiles>=0.8.0"
    ]
    
    print("📦 Installing async packages...")
    for package in async_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            print(f"⚠️ Failed to install {package}, continuing...")
    
    # Telegram
    print("📦 Installing Telegram client...")
    telethon_versions = ["telethon>=1.24.0,<1.35.0", "telethon>=1.24.0", "telethon==1.28.5"]
    for version in telethon_versions:
        if run_command(f"pip install '{version}'", f"Installing {version}"):
            break
    
    # QuotexPy - try multiple versions
    print("📦 Installing QuotexPy...")
    quotex_versions = ["1.0.38", "1.0.37", "1.0.36", "1.0.35"]
    quotex_installed = False
    
    for version in quotex_versions:
        if run_command(f"pip install quotexpy=={version}", f"Installing quotexpy {version}"):
            quotex_installed = True
            break
    
    if not quotex_installed:
        print("⚠️ Could not install quotexpy from PyPI, trying GitHub...")
        github_urls = [
            "git+https://github.com/SantiiRepair/quotexpy.git",
            "git+https://github.com/cleitonleonel/pyquotex.git"
        ]
        
        for url in github_urls:
            if run_command(f"pip install {url}", f"Installing from {url}"):
                quotex_installed = True
                break
    
    if not quotex_installed:
        print("❌ Could not install quotexpy. You may need to install it manually.")
        print("Try: pip install git+https://github.com/SantiiRepair/quotexpy.git")
    
    # Optional packages
    optional_packages = [
        "pandas>=1.3.0,<2.0.0",
        "numpy>=1.21.0,<2.0.0",
        "sqlalchemy>=1.4.0,<2.0.0",
        "cryptography>=3.4.8"
    ]
    
    print("📦 Installing optional packages...")
    for package in optional_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            print(f"⚠️ Optional package {package} failed, continuing...")

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
        ("quotexpy", "quotexpy OR quotex_api")
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
                        print(f"❌ {package}")
            else:
                __import__(module)
                print(f"✅ {package}")
                success_count += 1
        except ImportError:
            print(f"❌ {package}")
    
    print(f"\n📊 Test Results: {success_count}/{len(test_imports)} packages working")
    
    if success_count >= len(test_imports) - 1:  # Allow one failure
        print("✅ Installation looks good!")
        return True
    else:
        print("⚠️ Some packages are missing, but you can try to run the bot")
        return False

def main():
    """Main installation function"""
    print("🤖 QXBroker Auto Trading Bot - Legacy Installation")
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print("=" * 60)
    
    # Check Python version
    python_check = check_python_version()
    if python_check == False:
        return 1
    elif python_check == "modern":
        print("You can use the regular installation:")
        print("pip install -r requirements.txt")
        return 0
    
    # Create project structure
    create_project_structure()
    
    # Install packages
    install_legacy_packages()
    
    # Create .env file
    create_env_file()
    
    # Test installation
    test_installation()
    
    print("\n" + "=" * 60)
    print("✅ Legacy installation completed!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your credentials")
    print("2. Copy all the Python files to their respective folders")
    print("3. Run: python utils/telegram_setup.py (to setup Telegram)")
    print("4. Run: python test_installation.py (to test)")
    print("5. Run: python main.py (to start the bot)")
    
    print("\n⚠️  Important Notes:")
    print("- Make sure to copy all .py files to the correct folders")
    print("- Use PRACTICE mode first to test")
    print("- Check the Windows setup guide: SETUP_WINDOWS.md")
    
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