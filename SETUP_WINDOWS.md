# 🪟 Windows Setup Guide for QXBroker Auto Trading Bot

This guide will help you set up the QXBroker Auto Trading Bot on Windows.

## 📋 Prerequisites

### 1. Check Python Version

Open Command Prompt or PowerShell and run:
```cmd
python --version
```

**Required**: Python 3.8 or higher. If you don't have Python or have an older version:

1. Go to [python.org](https://www.python.org/downloads/)
2. Download Python 3.11 or 3.12 (recommended)
3. **Important**: Check "Add Python to PATH" during installation

### 2. Install Git (Optional but recommended)

Download from [git-scm.com](https://git-scm.com/download/win)

## 🚀 Quick Installation

### Method 1: Download and Setup

1. **Download the project files** to a folder (e.g., `C:\TradingBot\`)

2. **Open Command Prompt** in that folder:
   - Hold `Shift` + Right-click in the folder
   - Select "Open PowerShell window here" or "Open command window here"

3. **Run the installation script**:
   ```cmd
   python install.py
   ```

### Method 2: Manual Installation

If the automatic installation doesn't work:

1. **Install dependencies one by one**:
   ```cmd
   pip install requests python-dotenv colorama termcolor pytz
   pip install pydantic aiohttp websockets telethon
   pip install quotexpy
   ```

2. **If quotexpy fails**, try:
   ```cmd
   pip install git+https://github.com/SantiiRepair/quotexpy.git
   ```

3. **Create project structure**:
   ```cmd
   mkdir config core brokers telegram_integration trading utils
   ```

## ⚙️ Configuration

### 1. Create Environment File

Copy `.env.example` to `.env`:
```cmd
copy .env.example .env
```

### 2. Edit Configuration

Open `.env` in Notepad and fill in your details:

```env
# QXBroker Account
QXBROKER_EMAIL=your_email@example.com
QXBROKER_PASSWORD=your_password
QXBROKER_MODE=PRACTICE
QXBROKER_HOST=qxbroker.com

# Telegram API (Get from https://my.telegram.org/)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE_NUMBER=+1234567890
TELEGRAM_CHAT_ID=your_chat_id

# Trading Settings
DEFAULT_TRADE_AMOUNT=10.0
MARTINGALE_ENABLED=true
MAX_DAILY_LOSS=100.0
```

### 3. Get Telegram API Credentials

1. Go to [my.telegram.org](https://my.telegram.org/)
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Copy the `API ID` and `API Hash`

## 📱 Telegram Setup

Run the Telegram setup utility:
```cmd
python utils/telegram_setup.py
```

Follow the prompts to:
- Authenticate with Telegram
- Find chat IDs for signal monitoring
- Test signal parsing

## 🧪 Test Installation

```cmd
python test_installation.py
```

This will verify all dependencies are installed correctly.

## 🚀 Run the Bot

```cmd
python main.py
```

## 🛠️ Troubleshooting

### Common Windows Issues

#### "python is not recognized"
- Python is not in PATH
- Reinstall Python and check "Add to PATH"
- Or use full path: `C:\Python311\python.exe`

#### "pip is not recognized"
- Usually comes with Python
- Try: `python -m pip install package_name`

#### SSL Certificate errors
```cmd
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org package_name
```

#### Permission errors
- Run Command Prompt as Administrator
- Or use: `pip install --user package_name`

#### quotexpy installation fails
Try these alternatives:
```cmd
# Option 1: Older version
pip install quotexpy==1.0.38

# Option 2: From GitHub
pip install git+https://github.com/SantiiRepair/quotexpy.git

# Option 3: Manual download
# Download the quotexpy source and install locally
```

#### Module not found errors
Make sure you're in the correct directory:
```cmd
cd C:\path\to\your\trading\bot
python main.py
```

### Firewall Issues

If Windows Firewall blocks the connection:
1. Go to Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Add Python to the exceptions

### Antivirus Issues

Some antivirus software may flag the bot:
1. Add the bot folder to antivirus exceptions
2. Ensure the bot files aren't quarantined

## 📁 Recommended Folder Structure

```
C:\TradingBot\
├── main.py
├── .env
├── requirements.txt
├── config\
├── core\
├── brokers\
├── telegram_integration\
├── trading\
└── utils\
```

## 🔄 Starting the Bot Automatically

### Create a Batch File

Create `start_bot.bat`:
```batch
@echo off
cd /d "C:\path\to\your\trading\bot"
python main.py
pause
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., at startup)
4. Set action to start your batch file

## 📊 Monitoring

### View Logs
The bot creates `trading_bot.log` in the same folder. Open with Notepad to view logs.

### Stop the Bot
Press `Ctrl+C` in the command window.

## 🆘 Getting Help

If you encounter issues:

1. Check the log file: `trading_bot.log`
2. Run the test script: `python test_installation.py`
3. Try the Telegram setup: `python utils/telegram_setup.py`
4. Check your Python version: `python --version`
5. Verify all files are in place

## 🔐 Security Tips

1. **Never share your .env file**
2. **Use PRACTICE mode first**
3. **Set reasonable risk limits**
4. **Keep your credentials secure**
5. **Monitor the bot regularly**

---

**Happy Trading! 🚀📈**