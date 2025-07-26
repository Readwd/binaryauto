# 🤖 QXBroker Auto Trading Bot with Telegram Signal Integration

A powerful, fully-featured auto trading bot for QXBroker (Quotex) with advanced Telegram signal integration, comprehensive risk management, and martingale strategy support.

## ✨ Features

### 🎯 Core Trading Features
- **Multi-Broker Support**: QXBroker.com and Quotex.com
- **Real-time Signal Processing**: Advanced Telegram message parsing
- **Automated Trade Execution**: Seamless broker integration
- **Multiple Signal Formats**: Support for various signal patterns
- **Asset Validation**: Real-time market status checking

### 📊 Risk Management
- **Position Sizing**: Dynamic calculation based on balance and risk
- **Daily Loss Limits**: Configurable maximum daily loss protection
- **Concurrent Trade Limits**: Control maximum simultaneous positions
- **Consecutive Loss Protection**: Automatic trading pause after losses
- **Market Hours Filtering**: Trade only during specified hours

### 🎰 Martingale Strategy
- **Configurable Steps**: Set maximum martingale sequence length
- **Dynamic Multipliers**: Customizable progression ratios
- **Balance Protection**: Prevent over-leveraging
- **Sequence Tracking**: Complete martingale trade monitoring

### 📱 Telegram Integration
- **Real-time Monitoring**: Live signal detection from channels/groups
- **Multiple Chat Support**: Monitor multiple signal sources
- **Trade Notifications**: Instant result updates
- **Signal Validation**: Advanced parsing with confidence scoring
- **Message History**: Access to chat history for analysis

### 🔒 Security & Reliability
- **Connection Monitoring**: Automatic reconnection handling
- **Error Recovery**: Robust error handling and logging
- **Session Management**: Persistent trading sessions
- **Graceful Shutdown**: Safe termination with trade completion

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/qxbroker-trading-bot.git
cd qxbroker-trading-bot

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# QXBroker Configuration
QXBROKER_EMAIL=your_email@example.com
QXBROKER_PASSWORD=your_password
QXBROKER_MODE=PRACTICE  # PRACTICE or REAL
QXBROKER_HOST=qxbroker.com  # or quotex.com

# Telegram Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE_NUMBER=+1234567890
TELEGRAM_CHAT_ID=your_chat_id

# Trading Configuration
DEFAULT_TRADE_AMOUNT=10.0
MARTINGALE_ENABLED=true
MAX_DAILY_LOSS=500.0
```

### 3. Setup Telegram

Run the Telegram setup utility to authenticate and find chat IDs:

```bash
python utils/telegram_setup.py
```

Follow the interactive prompts to:
- Authenticate with Telegram
- Find chat IDs for signal monitoring
- Test signal parsing

### 4. Run the Bot

```bash
python main.py
```

## 📋 Configuration Options

### QXBroker Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `QXBROKER_EMAIL` | Your broker account email | Required |
| `QXBROKER_PASSWORD` | Your broker account password | Required |
| `QXBROKER_MODE` | Trading mode (PRACTICE/REAL) | PRACTICE |
| `QXBROKER_HOST` | Broker host (qxbroker.com/quotex.com) | qxbroker.com |

### Telegram Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `TELEGRAM_API_ID` | Telegram API ID from my.telegram.org | Required |
| `TELEGRAM_API_HASH` | Telegram API Hash | Required |
| `TELEGRAM_PHONE_NUMBER` | Your phone number with country code | Required |
| `TELEGRAM_CHAT_ID` | Chat ID to monitor for signals | Optional |

### Trading Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `DEFAULT_TRADE_AMOUNT` | Default trade amount in USD | 10.0 |
| `MAX_TRADE_AMOUNT` | Maximum allowed trade amount | 100.0 |
| `MIN_TRADE_AMOUNT` | Minimum allowed trade amount | 1.0 |
| `MARTINGALE_ENABLED` | Enable martingale strategy | true |
| `MARTINGALE_MULTIPLIER` | Martingale progression multiplier | 2.0 |
| `MAX_MARTINGALE_STEPS` | Maximum martingale steps | 3 |

### Risk Management
| Setting | Description | Default |
|---------|-------------|---------|
| `MAX_DAILY_LOSS` | Maximum daily loss limit | 500.0 |
| `MAX_CONCURRENT_TRADES` | Maximum simultaneous trades | 5 |
| `RISK_PERCENTAGE` | Risk percentage per trade | 2.0 |
| `MIN_SIGNAL_CONFIDENCE` | Minimum signal confidence | 70 |

## 📊 Supported Signal Formats

The bot supports multiple signal formats:

### Standard Format
```
EURUSD CALL $10 5M
GBPUSD PUT 15 3M
```

### Emoji Format
```
EURUSD 📈 5M
GBPUSD 📉 10 minutes
```

### Structured Format
```
Asset: EURUSD
Direction: CALL
Amount: $10
Duration: 5M
```

### Time-Based Format
```
EURUSD CALL at 14:30 for 5 minutes
```

### Keyword Detection
```
EURUSD going UP for 5 minutes
GBPUSD bearish trend, 10M
```

## 🎯 Supported Assets

- **Major Forex Pairs**: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD
- **Cross Pairs**: EURGBP, EURJPY, GBPJPY
- **OTC Variants**: All major pairs with _otc suffix (for QXBroker)

## 📈 Risk Management Features

### Position Sizing
- Dynamic calculation based on account balance
- Risk percentage limiting
- Consecutive loss reduction
- Balance protection

### Daily Limits
- Maximum daily loss protection
- Trade count limits
- Automatic trading suspension
- Daily metric reset

### Martingale Management
- Configurable sequence length
- Balance-based limits
- Sequence tracking
- Automatic completion

## 🔧 Advanced Usage

### Custom Signal Parsing

You can extend the signal parser to support custom formats:

```python
from telegram_integration import TelegramSignalParser

parser = TelegramSignalParser()

# Add custom pattern
custom_pattern = re.compile(r'YOUR_PATTERN_HERE')
parser.signal_patterns['custom'] = custom_pattern
```

### Risk Manager Customization

```python
from trading import RiskManager

risk_manager = RiskManager()

# Custom risk rules
async def custom_risk_check(signal, balance):
    # Your custom risk logic here
    return True, "Approved"

risk_manager.custom_checks.append(custom_risk_check)
```

### Event Callbacks

```python
async def on_trade_completed(trade):
    print(f"Trade completed: {trade.status}")

async def on_signal_received(signal):
    print(f"Signal received: {signal.asset}")

bot.set_trade_callback(on_trade_completed)
bot.set_signal_callback(on_signal_received)
```

## 📊 Monitoring & Statistics

The bot provides comprehensive statistics:

### Real-time Status
- Connection status (Broker & Telegram)
- Account balance and P&L
- Active trades count
- Win rate and performance metrics

### Trading Statistics
- Total signals received
- Trades executed, won, lost
- Daily profit/loss
- Risk metrics

### Session Management
- Trading session tracking
- Performance analysis
- Maximum drawdown
- Win rate calculation

## 🛠️ Troubleshooting

### Common Issues

**Connection Failed**
```bash
# Check credentials in .env file
# Verify internet connection
# Try different broker host
```

**Telegram Authentication**
```bash
# Run telegram setup utility
python utils/telegram_setup.py

# Check API credentials
# Verify phone number format
```

**No Signals Detected**
```bash
# Test signal parsing
python utils/telegram_setup.py
# Select option 2 to test parsing

# Check allowed assets in config
# Verify chat ID is correct
```

**Trade Execution Failed**
```bash
# Check broker connection
# Verify account balance
# Check asset market hours
# Review risk management settings
```

### Logging

The bot provides detailed logging. Check the log file for detailed information:

```bash
tail -f trading_bot.log
```

Log levels can be configured in `.env`:
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🔐 Security Considerations

1. **Never share your API credentials**
2. **Use PRACTICE mode for testing**
3. **Set appropriate risk limits**
4. **Monitor the bot regularly**
5. **Keep your environment file secure**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Trading involves risk. This bot is for educational purposes only. Past performance does not guarantee future results. Always trade responsibly and never risk more than you can afford to lose.**

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-username/qxbroker-trading-bot/issues) page
2. Review the troubleshooting section
3. Create a new issue with detailed information

## 🙏 Acknowledgments

- [quotexpy](https://github.com/SantiiRepair/quotexpy) - QXBroker API integration
- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram client library
- All contributors and testers

---

**Happy Trading! 🚀📈**