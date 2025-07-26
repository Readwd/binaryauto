#!/usr/bin/env python3
"""
QXBroker Auto Trading Bot Installation Script
This script will set up the project in your current directory
"""
import os
import sys
import subprocess
import urllib.request
import json

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print("✅ Python version is compatible")
    return True

def install_basic_requirements():
    """Install basic requirements that work with older Python versions"""
    basic_requirements = [
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
        "colorama>=0.4.4",
        "termcolor>=1.1.0",
        "pytz>=2021.1",
        "pydantic>=1.8.0,<2.0.0",  # Use v1 for compatibility
        "aiohttp>=3.7.0",
        "websockets>=10.0",
        "telethon>=1.24.0"
    ]
    
    print("📦 Installing basic requirements...")
    for req in basic_requirements:
        if not run_command(f"pip install {req}", f"Installing {req.split('>=')[0]}"):
            return False
    
    # Try to install quotexpy
    print("📦 Installing quotexpy...")
    quotex_versions = ["1.0.38", "1.0.37", "1.0.36", "1.0.35"]
    
    for version in quotex_versions:
        if run_command(f"pip install quotexpy=={version}", f"Installing quotexpy {version}"):
            print(f"✅ Successfully installed quotexpy {version}")
            break
    else:
        print("⚠️ Could not install quotexpy, trying alternative...")
        if not run_command("pip install git+https://github.com/SantiiRepair/quotexpy.git", "Installing quotexpy from GitHub"):
            print("❌ Failed to install quotexpy. You may need to install it manually.")
    
    return True

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
                f.write(f'"""{directory.title()} module"""\n')
    
    print("✅ Project structure created")
    return True

def create_env_file():
    """Create .env file from example"""
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        print("📝 Creating .env file from template...")
        with open(".env.example", "r") as src, open(".env", "w") as dst:
            dst.write(src.read())
        print("✅ .env file created. Please edit it with your credentials.")
    return True

def main():
    """Main installation function"""
    print("🤖 QXBroker Auto Trading Bot - Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create project structure
    if not create_project_structure():
        return 1
    
    # Install requirements
    if not install_basic_requirements():
        print("⚠️ Some packages failed to install, but continuing...")
    
    # Create .env file
    create_env_file()
    
    print("\n" + "=" * 50)
    print("✅ Installation completed!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your credentials")
    print("2. Run: python utils/telegram_setup.py")
    print("3. Run: python main.py")
    print("\n🚀 Happy trading!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())