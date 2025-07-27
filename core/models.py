"""
Data models for QXBroker Auto Trading Bot
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

# Try to import pydantic with compatibility for v1 and v2
try:
    from pydantic import BaseModel, validator, ConfigDict
    PYDANTIC_V2 = True
except ImportError:
    try:
        from pydantic import BaseModel, validator
        from pydantic import Config as ConfigDict
        PYDANTIC_V2 = False
    except ImportError:
        # Fallback for very old versions or if pydantic is not available
        class BaseModel:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
            
            def dict(self):
                return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        
        def validator(field_name, **kwargs):
            def decorator(func):
                return func
            return decorator
        
        class ConfigDict:
            pass
        
        PYDANTIC_V2 = False

class TradeDirection(str, Enum):
    """Trade direction enum"""
    CALL = "call"
    PUT = "put"

class TradeStatus(str, Enum):
    """Trade status enum"""
    PENDING = "pending"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"
    ERROR = "error"

class SignalSource(str, Enum):
    """Signal source enum"""
    TELEGRAM = "telegram"
    MANUAL = "manual"
    API = "api"

class TradingSignal(BaseModel):
    """Trading signal model"""
    id: Optional[str] = None
    asset: str
    direction: TradeDirection
    amount: float
    duration: int  # in seconds
    confidence: Optional[int] = None  # percentage
    source: SignalSource = SignalSource.TELEGRAM
    timestamp: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

    def __init__(self, **data):
        if data.get('id') is None:
            data['id'] = str(uuid.uuid4())
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now()
        if data.get('metadata') is None:
            data['metadata'] = {}
        super().__init__(**data)

    if PYDANTIC_V2:
        @validator('amount')
        @classmethod
        def validate_amount(cls, v):
            if v <= 0:
                raise ValueError('Amount must be positive')
            return v

        @validator('duration')
        @classmethod
        def validate_duration(cls, v):
            if v <= 0:
                raise ValueError('Duration must be positive')
            return v

        @validator('confidence')
        @classmethod
        def validate_confidence(cls, v):
            if v is not None and (v < 0 or v > 100):
                raise ValueError('Confidence must be between 0 and 100')
            return v
    else:
        @validator('amount')
        def validate_amount(cls, v):
            if v <= 0:
                raise ValueError('Amount must be positive')
            return v

        @validator('duration')
        def validate_duration(cls, v):
            if v <= 0:
                raise ValueError('Duration must be positive')
            return v

        @validator('confidence')
        def validate_confidence(cls, v):
            if v is not None and (v < 0 or v > 100):
                raise ValueError('Confidence must be between 0 and 100')
            return v

class Trade(BaseModel):
    """Trade model"""
    id: Optional[str] = None
    signal_id: str
    broker_trade_id: Optional[str] = None
    asset: str
    direction: TradeDirection
    amount: float
    duration: int
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    status: TradeStatus = TradeStatus.PENDING
    profit_loss: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    martingale_step: int = 0
    metadata: Dict[str, Any] = {}

    def __init__(self, **data):
        if data.get('id') is None:
            data['id'] = str(uuid.uuid4())
        if data.get('start_time') is None:
            data['start_time'] = datetime.now()
        if data.get('metadata') is None:
            data['metadata'] = {}
        super().__init__(**data)

    if PYDANTIC_V2:
        @validator('amount')
        @classmethod
        def validate_amount(cls, v):
            if v <= 0:
                raise ValueError('Amount must be positive')
            return v
    else:
        @validator('amount')
        def validate_amount(cls, v):
            if v <= 0:
                raise ValueError('Amount must be positive')
            return v

class TradingSession(BaseModel):
    """Trading session model"""
    id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit_loss: float = 0.0
    max_drawdown: float = 0.0
    balance_start: float = 0.0
    balance_end: Optional[float] = None

    def __init__(self, **data):
        if data.get('id') is None:
            data['id'] = str(uuid.uuid4())
        if data.get('start_time') is None:
            data['start_time'] = datetime.now()
        super().__init__(**data)

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def is_active(self) -> bool:
        """Check if session is active"""
        return self.end_time is None

class RiskMetrics(BaseModel):
    """Risk management metrics"""
    daily_loss: float = 0.0
    daily_profit: float = 0.0
    concurrent_trades: int = 0
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    total_trades_today: int = 0
    last_trade_time: Optional[datetime] = None

    @property
    def daily_pnl(self) -> float:
        """Calculate daily profit and loss"""
        return self.daily_profit - self.daily_loss

    def reset_daily_metrics(self):
        """Reset daily metrics"""
        self.daily_loss = 0.0
        self.daily_profit = 0.0
        self.total_trades_today = 0
        self.consecutive_losses = 0

class BrokerConnection(BaseModel):
    """Broker connection status model"""
    is_connected: bool = False
    last_ping: Optional[datetime] = None
    connection_attempts: int = 0
    last_error: Optional[str] = None
    balance: Optional[float] = None
    account_type: Optional[str] = None  # PRACTICE or REAL

    def update_connection_status(self, connected: bool, error: str = None):
        """Update connection status"""
        self.is_connected = connected
        self.last_ping = datetime.now()
        if error:
            self.last_error = error
            self.connection_attempts += 1

class TelegramMessage(BaseModel):
    """Telegram message model"""
    message_id: int
    chat_id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    text: str
    timestamp: datetime
    is_signal: bool = False
    parsed_signal: Optional[TradingSignal] = None

    if PYDANTIC_V2:
        @validator('text')
        @classmethod
        def validate_text(cls, v):
            if not v or not v.strip():
                raise ValueError('Text cannot be empty')
            return v.strip()
    else:
        @validator('text')
        def validate_text(cls, v):
            if not v or not v.strip():
                raise ValueError('Text cannot be empty')
            return v.strip()

class MartingaleSequence(BaseModel):
    """Martingale sequence tracking"""
    sequence_id: Optional[str] = None
    original_signal_id: str
    current_step: int = 0
    max_steps: int = 3
    base_amount: float
    current_amount: Optional[float] = None
    total_invested: float = 0.0
    trades: List[str] = []  # Trade IDs
    is_complete: bool = False
    final_result: Optional[TradeStatus] = None

    def __init__(self, **data):
        if data.get('sequence_id') is None:
            data['sequence_id'] = str(uuid.uuid4())
        if data.get('current_amount') is None:
            data['current_amount'] = data.get('base_amount', 0.0)
        if data.get('trades') is None:
            data['trades'] = []
        super().__init__(**data)

    def next_step(self, multiplier: float = 2.0) -> float:
        """Calculate next martingale amount"""
        if self.current_step >= self.max_steps:
            raise ValueError("Maximum martingale steps reached")

        self.current_step += 1
        self.current_amount = self.base_amount * (multiplier ** self.current_step)
        return self.current_amount

    def add_trade(self, trade_id: str, amount: float):
        """Add trade to sequence"""
        self.trades.append(trade_id)
        self.total_invested += amount

    def complete_sequence(self, result: TradeStatus):
        """Complete the martingale sequence"""
        self.is_complete = True
        self.final_result = result

class AlertConfig(BaseModel):
    """Alert configuration model"""
    telegram_alerts: bool = True
    email_alerts: bool = False
    discord_alerts: bool = False
    win_alerts: bool = True
    loss_alerts: bool = True
    error_alerts: bool = True
    balance_alerts: bool = True
    daily_summary: bool = True

    if PYDANTIC_V2:
        model_config = ConfigDict(
            json_encoders={
                datetime: lambda v: v.isoformat() if v else None
            }
        )
    else:
        class Config:
            json_encoders = {
                datetime: lambda v: v.isoformat() if v else None
            }