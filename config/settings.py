"""
Configuration settings for QXBroker Auto Trading Bot
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

# Try to import pydantic with compatibility for v1 and v2
try:
    from pydantic import BaseSettings, validator
    PYDANTIC_V2 = False
except ImportError:
    try:
        from pydantic.v1 import BaseSettings, validator
        PYDANTIC_V2 = True
    except ImportError:
        # Fallback for very old versions
        try:
            from pydantic import BaseModel as BaseSettings
            from pydantic import validator
            PYDANTIC_V2 = False
        except ImportError:
            # If pydantic is not available, create a simple class
            class BaseSettings:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            def validator(field_name, **kwargs):
                def decorator(func):
                    return func
                return decorator
            
            PYDANTIC_V2 = False

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # QXBroker Configuration
    qxbroker_email: str = os.getenv("QXBROKER_EMAIL", "")
    qxbroker_password: str = os.getenv("QXBROKER_PASSWORD", "")
    qxbroker_mode: str = os.getenv("QXBROKER_MODE", "PRACTICE")
    qxbroker_host: str = os.getenv("QXBROKER_HOST", "qxbroker.com")
    
    # Telegram Configuration
    telegram_api_id: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    telegram_api_hash: str = os.getenv("TELEGRAM_API_HASH", "")
    telegram_phone_number: str = os.getenv("TELEGRAM_PHONE_NUMBER", "")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Trading Configuration
    default_trade_amount: float = float(os.getenv("DEFAULT_TRADE_AMOUNT", "10.0"))
    max_trade_amount: float = float(os.getenv("MAX_TRADE_AMOUNT", "100.0"))
    min_trade_amount: float = float(os.getenv("MIN_TRADE_AMOUNT", "1.0"))
    martingale_enabled: bool = os.getenv("MARTINGALE_ENABLED", "true").lower() == "true"
    martingale_multiplier: float = float(os.getenv("MARTINGALE_MULTIPLIER", "2.0"))
    max_martingale_steps: int = int(os.getenv("MAX_MARTINGALE_STEPS", "3"))
    stop_loss_percentage: float = float(os.getenv("STOP_LOSS_PERCENTAGE", "10.0"))
    take_profit_percentage: float = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "20.0"))
    
    # Risk Management
    max_daily_loss: float = float(os.getenv("MAX_DAILY_LOSS", "500.0"))
    max_concurrent_trades: int = int(os.getenv("MAX_CONCURRENT_TRADES", "5"))
    risk_percentage: float = float(os.getenv("RISK_PERCENTAGE", "2.0"))
    
    # Signal Processing
    signal_timeout: int = int(os.getenv("SIGNAL_TIMEOUT", "300"))
    min_signal_confidence: int = int(os.getenv("MIN_SIGNAL_CONFIDENCE", "70"))
    allowed_assets: List[str] = os.getenv("ALLOWED_ASSETS", "EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD").split(",")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "trading_bot.log")
    
    def __init__(self, **kwargs):
        """Initialize settings with error handling"""
        try:
            super().__init__(**kwargs)
        except Exception:
            # Fallback initialization for compatibility
            for key, value in kwargs.items():
                setattr(self, key, value)
            
            # Set defaults if not provided
            if not hasattr(self, 'qxbroker_email'):
                self.qxbroker_email = os.getenv("QXBROKER_EMAIL", "")
            if not hasattr(self, 'qxbroker_password'):
                self.qxbroker_password = os.getenv("QXBROKER_PASSWORD", "")
            if not hasattr(self, 'qxbroker_mode'):
                self.qxbroker_mode = os.getenv("QXBROKER_MODE", "PRACTICE")
            if not hasattr(self, 'qxbroker_host'):
                self.qxbroker_host = os.getenv("QXBROKER_HOST", "qxbroker.com")
            
            # Set other defaults
            self._set_defaults()
    
    def _set_defaults(self):
        """Set default values for all settings"""
        defaults = {
            'telegram_api_id': int(os.getenv("TELEGRAM_API_ID", "0")),
            'telegram_api_hash': os.getenv("TELEGRAM_API_HASH", ""),
            'telegram_phone_number': os.getenv("TELEGRAM_PHONE_NUMBER", ""),
            'telegram_bot_token': os.getenv("TELEGRAM_BOT_TOKEN", ""),
            'telegram_chat_id': os.getenv("TELEGRAM_CHAT_ID", ""),
            'default_trade_amount': float(os.getenv("DEFAULT_TRADE_AMOUNT", "10.0")),
            'max_trade_amount': float(os.getenv("MAX_TRADE_AMOUNT", "100.0")),
            'min_trade_amount': float(os.getenv("MIN_TRADE_AMOUNT", "1.0")),
            'martingale_enabled': os.getenv("MARTINGALE_ENABLED", "true").lower() == "true",
            'martingale_multiplier': float(os.getenv("MARTINGALE_MULTIPLIER", "2.0")),
            'max_martingale_steps': int(os.getenv("MAX_MARTINGALE_STEPS", "3")),
            'stop_loss_percentage': float(os.getenv("STOP_LOSS_PERCENTAGE", "10.0")),
            'take_profit_percentage': float(os.getenv("TAKE_PROFIT_PERCENTAGE", "20.0")),
            'max_daily_loss': float(os.getenv("MAX_DAILY_LOSS", "500.0")),
            'max_concurrent_trades': int(os.getenv("MAX_CONCURRENT_TRADES", "5")),
            'risk_percentage': float(os.getenv("RISK_PERCENTAGE", "2.0")),
            'signal_timeout': int(os.getenv("SIGNAL_TIMEOUT", "300")),
            'min_signal_confidence': int(os.getenv("MIN_SIGNAL_CONFIDENCE", "70")),
            'allowed_assets': os.getenv("ALLOWED_ASSETS", "EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD").split(","),
            'database_url': os.getenv("DATABASE_URL", "sqlite:///trading_bot.db"),
            'log_level': os.getenv("LOG_LEVEL", "INFO"),
            'log_file': os.getenv("LOG_FILE", "trading_bot.log")
        }
        
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)
    
    @validator('qxbroker_mode')
    def validate_mode(cls, v):
        if v not in ['PRACTICE', 'REAL']:
            print(f"Warning: Invalid qxbroker_mode '{v}', using 'PRACTICE'")
            return 'PRACTICE'
        return v
    
    @validator('qxbroker_host')
    def validate_host(cls, v):
        if v not in ['qxbroker.com', 'quotex.com']:
            print(f"Warning: Invalid qxbroker_host '{v}', using 'qxbroker.com'")
            return 'qxbroker.com'
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        if v not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            print(f"Warning: Invalid log_level '{v}', using 'INFO'")
            return 'INFO'
        return v

    if hasattr(BaseSettings, 'Config'):
        class Config:
            env_file = ".env"
            case_sensitive = False

# Create settings instance with error handling
try:
    settings = Settings()
except Exception as e:
    print(f"Warning: Error creating settings: {e}")
    print("Using fallback settings initialization...")
    
    # Fallback settings creation
    class FallbackSettings:
        def __init__(self):
            self.qxbroker_email = os.getenv("QXBROKER_EMAIL", "")
            self.qxbroker_password = os.getenv("QXBROKER_PASSWORD", "")
            self.qxbroker_mode = os.getenv("QXBROKER_MODE", "PRACTICE")
            self.qxbroker_host = os.getenv("QXBROKER_HOST", "qxbroker.com")
            
            self.telegram_api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
            self.telegram_api_hash = os.getenv("TELEGRAM_API_HASH", "")
            self.telegram_phone_number = os.getenv("TELEGRAM_PHONE_NUMBER", "")
            self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
            
            self.default_trade_amount = float(os.getenv("DEFAULT_TRADE_AMOUNT", "10.0"))
            self.max_trade_amount = float(os.getenv("MAX_TRADE_AMOUNT", "100.0"))
            self.min_trade_amount = float(os.getenv("MIN_TRADE_AMOUNT", "1.0"))
            self.martingale_enabled = os.getenv("MARTINGALE_ENABLED", "true").lower() == "true"
            self.martingale_multiplier = float(os.getenv("MARTINGALE_MULTIPLIER", "2.0"))
            self.max_martingale_steps = int(os.getenv("MAX_MARTINGALE_STEPS", "3"))
            self.stop_loss_percentage = float(os.getenv("STOP_LOSS_PERCENTAGE", "10.0"))
            self.take_profit_percentage = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "20.0"))
            
            self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", "500.0"))
            self.max_concurrent_trades = int(os.getenv("MAX_CONCURRENT_TRADES", "5"))
            self.risk_percentage = float(os.getenv("RISK_PERCENTAGE", "2.0"))
            
            self.signal_timeout = int(os.getenv("SIGNAL_TIMEOUT", "300"))
            self.min_signal_confidence = int(os.getenv("MIN_SIGNAL_CONFIDENCE", "70"))
            self.allowed_assets = os.getenv("ALLOWED_ASSETS", "EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD").split(",")
            
            self.database_url = os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")
            self.log_level = os.getenv("LOG_LEVEL", "INFO")
            self.log_file = os.getenv("LOG_FILE", "trading_bot.log")
    
    settings = FallbackSettings()

# Trading pairs mapping for different brokers
ASSET_MAPPING = {
    'qxbroker.com': {
        'EURUSD': 'EURUSD_otc',
        'GBPUSD': 'GBPUSD_otc',
        'USDJPY': 'USDJPY_otc',
        'AUDUSD': 'AUDUSD_otc',
        'USDCAD': 'USDCAD_otc',
        'EURGBP': 'EURGBP_otc',
        'EURJPY': 'EURJPY_otc',
        'GBPJPY': 'GBPJPY_otc',
    },
    'quotex.com': {
        'EURUSD': 'EURUSD',
        'GBPUSD': 'GBPUSD',
        'USDJPY': 'USDJPY',
        'AUDUSD': 'AUDUSD',
        'USDCAD': 'USDCAD',
        'EURGBP': 'EURGBP',
        'EURJPY': 'EURJPY',
        'GBPJPY': 'GBPJPY',
    }
}

# Signal keywords for different directions
SIGNAL_KEYWORDS = {
    'call': ['call', 'buy', 'up', 'higher', 'bullish', '📈', '🟢', '⬆️'],
    'put': ['put', 'sell', 'down', 'lower', 'bearish', '📉', '🔴', '⬇️']
}

# Time frame mappings
TIMEFRAME_MAPPING = {
    '1m': 60,
    '2m': 120,
    '3m': 180,
    '5m': 300,
    '10m': 600,
    '15m': 900,
    '30m': 1800,
    '1h': 3600
}