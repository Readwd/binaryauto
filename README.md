# QXBroker Auto Trading Bot

An automated trading bot that listens for Telegram signals and automatically places trades on qxbroker.com.

## Features

- **Telegram Signal Integration**: Listens for trading signals from Telegram channels/groups
- **Automatic Trading**: Places trades automatically on qxbroker.com based on received signals
- **Signal Parsing**: Extracts trading pair, direction, expiration, and time from signal messages
- **Visible Browser**: Runs with visible browser for debugging and monitoring
- **Secure Credentials**: Supports environment variables for secure credential storage

## Signal Format

The bot expects signals in this format:
```
====== SINAL ======
╭━━━━━━━・━━━━━━━╮
🐲 Active Pair -» EURJPY
🕓 Timetable  -» 23:14
⏳ Expiration  -» M1
🔴 Direction   -» PUT
╰━━━━━━━・━━━━━━━╯
📳 Signal Sent Successfully
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Chrome WebDriver
Make sure you have Chrome browser installed and ChromeDriver available in your PATH.

### 3. Create Telegram Bot
1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Get your bot token
4. Add your bot to the channel/group where signals are posted

### 4. Configure Credentials (Optional)
Create a `.env` file with your credentials:
```
QX_USERNAME=your_qxbroker_username
QX_PASSWORD=your_qxbroker_password
TELEGRAM_TOKEN=your_telegram_bot_token
```

### 5. Run the Bot
```bash
python main.py
```

The bot will prompt you for:
- qxbroker.com username and password (if not in .env)
- Trade amount
- Telegram bot token (if not in .env)

## How It Works

1. **Signal Detection**: Bot listens for messages containing "Active Pair" and "Direction"
2. **Signal Parsing**: Extracts trading details from the message
3. **Browser Automation**: 
   - Logs in to qxbroker.com
   - Navigates to trading page
   - Selects the trading pair
   - Sets expiration time
   - Sets trade amount
   - Places CALL or PUT trade
4. **Confirmation**: Prints trade details and success status

## Trading Process

When a signal is received, the bot will:
1. Login to qxbroker.com (if not already logged in)
2. Navigate to the trading interface
3. Select the specified trading pair (e.g., EURJPY)
4. Set the expiration time (e.g., M1 = 1 minute)
5. Set the trade amount (specified at startup)
6. Place the trade in the specified direction (CALL or PUT)
7. Display confirmation with all trade details

## Security Notes

- Store credentials in `.env` file (not committed to version control)
- The bot runs with visible browser for monitoring
- Review all trades before they are placed
- Test with small amounts first

## Troubleshooting

- **Login Issues**: Check username/password and ensure qxbroker.com is accessible
- **Element Not Found**: The website structure may have changed; update selectors
- **Telegram Issues**: Ensure bot token is correct and bot has access to the channel

## Disclaimer

This bot is for educational purposes. Trading involves risk. Use at your own discretion and ensure compliance with qxbroker.com's terms of service.