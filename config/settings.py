"""
Configuration settings for QXBroker Auto Trading Bot
"""
import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

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
    
    @validator('qxbroker_mode')
    def validate_mode(cls, v):
        if v not in ['PRACTICE', 'REAL']:
            raise ValueError('qxbroker_mode must be either PRACTICE or REAL')
        return v
    
    @validator('qxbroker_host')
    def validate_host(cls, v):
        if v not in ['qxbroker.com', 'quotex.com']:
            raise ValueError('qxbroker_host must be either qxbroker.com or quotex.com')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        if v not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError('log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL')
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

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