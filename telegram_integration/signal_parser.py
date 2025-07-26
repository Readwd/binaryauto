"""
Telegram signal parser for extracting trading signals from messages
"""
import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pytz

from config import settings, SIGNAL_KEYWORDS, TIMEFRAME_MAPPING
from core.models import TradingSignal, TradeDirection, SignalSource

logger = logging.getLogger(__name__)

class TelegramSignalParser:
    """Parser for extracting trading signals from Telegram messages"""
    
    def __init__(self):
        self.signal_patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for signal detection"""
        patterns = {}
        
        # Pattern 1: Asset Direction Amount Duration
        # Example: "EURUSD CALL $10 5M"
        patterns['standard'] = re.compile(
            r'(?P<asset>[A-Z]{6})\s+(?P<direction>CALL|PUT|BUY|SELL|UP|DOWN)\s*'
            r'(?:\$?(?P<amount>\d+(?:\.\d+)?))?\s*'
            r'(?P<duration>\d+[MH]?)',
            re.IGNORECASE
        )
        
        # Pattern 2: Emoji-based signals
        # Example: "EURUSD 📈 5M" or "GBPUSD ⬆️ 10 minutes"
        patterns['emoji'] = re.compile(
            r'(?P<asset>[A-Z]{6})\s*(?P<direction>[📈📉🟢🔴⬆️⬇️])\s*'
            r'(?:\$?(?P<amount>\d+(?:\.\d+)?))?\s*'
            r'(?P<duration>\d+)\s*(?:M|MIN|MINUTES?|H|HOURS?)?',
            re.IGNORECASE
        )
        
        # Pattern 3: Structured format
        # Example: "Asset: EURUSD\nDirection: CALL\nAmount: $10\nDuration: 5M"
        patterns['structured'] = re.compile(
            r'Asset:\s*(?P<asset>[A-Z]{6})\s*'
            r'Direction:\s*(?P<direction>CALL|PUT|BUY|SELL|UP|DOWN)\s*'
            r'(?:Amount:\s*\$?(?P<amount>\d+(?:\.\d+)?)\s*)?'
            r'Duration:\s*(?P<duration>\d+[MH]?)',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Pattern 4: Time-based signals
        # Example: "EURUSD CALL at 14:30 for 5 minutes"
        patterns['timed'] = re.compile(
            r'(?P<asset>[A-Z]{6})\s+(?P<direction>CALL|PUT|BUY|SELL|UP|DOWN)\s+'
            r'(?:at\s+(?P<time>\d{1,2}:\d{2}))?\s*'
            r'(?:for\s+)?(?P<duration>\d+)\s*(?:M|MIN|MINUTES?)',
            re.IGNORECASE
        )
        
        # Pattern 5: Simple format
        # Example: "EURUSD UP 5M" or "GBPUSD DOWN"
        patterns['simple'] = re.compile(
            r'(?P<asset>[A-Z]{6})\s+(?P<direction>UP|DOWN|CALL|PUT|BUY|SELL)\s*'
            r'(?P<duration>\d+[MH]?)?',
            re.IGNORECASE
        )
        
        return patterns
    
    def parse_message(self, message_text: str) -> Optional[TradingSignal]:
        """Parse a Telegram message for trading signals"""
        try:
            message_text = message_text.strip()
            
            # Try each pattern
            for pattern_name, pattern in self.signal_patterns.items():
                match = pattern.search(message_text)
                if match:
                    logger.debug(f"Signal matched pattern '{pattern_name}': {match.groupdict()}")
                    
                    signal = self._extract_signal_from_match(match, message_text)
                    if signal:
                        logger.info(f"Parsed signal: {signal.asset} {signal.direction} ${signal.amount} {signal.duration}s")
                        return signal
            
            # Check for keyword-based detection
            signal = self._parse_keyword_signal(message_text)
            if signal:
                return signal
            
            logger.debug(f"No signal pattern matched for message: {message_text[:100]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing message: {str(e)}")
            return None
    
    def _extract_signal_from_match(self, match: re.Match, original_text: str) -> Optional[TradingSignal]:
        """Extract trading signal from regex match"""
        try:
            groups = match.groupdict()
            
            # Extract asset
            asset = groups.get('asset', '').upper()
            if not asset or asset not in settings.allowed_assets:
                logger.debug(f"Asset '{asset}' not in allowed assets")
                return None
            
            # Extract direction
            direction_str = groups.get('direction', '').upper()
            direction = self._parse_direction(direction_str)
            if not direction:
                logger.debug(f"Could not parse direction: {direction_str}")
                return None
            
            # Extract amount
            amount_str = groups.get('amount')
            if amount_str:
                amount = float(amount_str)
            else:
                amount = settings.default_trade_amount
            
            # Validate amount
            if amount < settings.min_trade_amount or amount > settings.max_trade_amount:
                logger.warning(f"Amount {amount} outside allowed range")
                amount = max(settings.min_trade_amount, min(amount, settings.max_trade_amount))
            
            # Extract duration
            duration_str = groups.get('duration', '5M')
            duration = self._parse_duration(duration_str)
            if not duration:
                logger.debug(f"Could not parse duration: {duration_str}")
                return None
            
            # Extract confidence (if mentioned in text)
            confidence = self._extract_confidence(original_text)
            
            # Extract expiry time (if mentioned)
            expiry_time = self._extract_expiry_time(original_text, groups.get('time'))
            
            return TradingSignal(
                asset=asset,
                direction=direction,
                amount=amount,
                duration=duration,
                confidence=confidence,
                source=SignalSource.TELEGRAM,
                expiry_time=expiry_time,
                metadata={
                    'original_text': original_text,
                    'pattern_match': groups
                }
            )
            
        except Exception as e:
            logger.error(f"Error extracting signal from match: {str(e)}")
            return None
    
    def _parse_keyword_signal(self, message_text: str) -> Optional[TradingSignal]:
        """Parse signal using keyword detection"""
        try:
            text_upper = message_text.upper()
            
            # Find asset
            asset = None
            for allowed_asset in settings.allowed_assets:
                if allowed_asset in text_upper:
                    asset = allowed_asset
                    break
            
            if not asset:
                return None
            
            # Find direction
            direction = None
            for dir_key, keywords in SIGNAL_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.upper() in text_upper or keyword in message_text:
                        direction = TradeDirection(dir_key)
                        break
                if direction:
                    break
            
            if not direction:
                return None
            
            # Extract numbers for amount and duration
            numbers = re.findall(r'\d+(?:\.\d+)?', message_text)
            
            amount = settings.default_trade_amount
            duration = 300  # 5 minutes default
            
            if numbers:
                # Try to determine which number is amount and which is duration
                for num_str in numbers:
                    num = float(num_str)
                    if 1 <= num <= 1000:  # Likely amount
                        amount = num
                    elif 60 <= num <= 3600:  # Likely duration in seconds
                        duration = int(num)
                    elif 1 <= num <= 60:  # Likely duration in minutes
                        duration = int(num * 60)
            
            # Validate amount
            amount = max(settings.min_trade_amount, min(amount, settings.max_trade_amount))
            
            return TradingSignal(
                asset=asset,
                direction=direction,
                amount=amount,
                duration=duration,
                source=SignalSource.TELEGRAM,
                metadata={
                    'original_text': message_text,
                    'parsing_method': 'keyword_detection'
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing keyword signal: {str(e)}")
            return None
    
    def _parse_direction(self, direction_str: str) -> Optional[TradeDirection]:
        """Parse direction string to TradeDirection enum"""
        direction_str = direction_str.upper()
        
        call_keywords = ['CALL', 'BUY', 'UP', 'HIGHER', 'BULLISH', '📈', '🟢', '⬆️']
        put_keywords = ['PUT', 'SELL', 'DOWN', 'LOWER', 'BEARISH', '📉', '🔴', '⬇️']
        
        if direction_str in call_keywords or direction_str in SIGNAL_KEYWORDS['call']:
            return TradeDirection.CALL
        elif direction_str in put_keywords or direction_str in SIGNAL_KEYWORDS['put']:
            return TradeDirection.PUT
        
        return None
    
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration string to seconds"""
        if not duration_str:
            return 300  # Default 5 minutes
        
        # Remove non-alphanumeric characters except for M, H
        duration_str = re.sub(r'[^0-9MH]', '', duration_str.upper())
        
        # Extract number and unit
        match = re.match(r'(\d+)([MH]?)', duration_str)
        if not match:
            return None
        
        number = int(match.group(1))
        unit = match.group(2) or 'M'  # Default to minutes
        
        if unit == 'M':
            return number * 60  # Convert minutes to seconds
        elif unit == 'H':
            return number * 3600  # Convert hours to seconds
        
        # If no unit, assume it's already in seconds if > 60, otherwise minutes
        if number > 60:
            return number
        else:
            return number * 60
    
    def _extract_confidence(self, text: str) -> Optional[int]:
        """Extract confidence percentage from text"""
        # Look for patterns like "85%", "confidence: 90", etc.
        confidence_patterns = [
            r'(\d+)%',
            r'confidence[:\s]+(\d+)',
            r'accuracy[:\s]+(\d+)',
            r'win rate[:\s]+(\d+)'
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                confidence = int(match.group(1))
                if 0 <= confidence <= 100:
                    return confidence
        
        return None
    
    def _extract_expiry_time(self, text: str, time_str: Optional[str]) -> Optional[datetime]:
        """Extract expiry time from text"""
        if not time_str:
            return None
        
        try:
            # Parse time string (e.g., "14:30")
            time_match = re.match(r'(\d{1,2}):(\d{2})', time_str)
            if not time_match:
                return None
            
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            
            # Create datetime for today at specified time
            now = datetime.now(pytz.UTC)
            expiry = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If the time has already passed today, assume it's for tomorrow
            if expiry <= now:
                expiry += timedelta(days=1)
            
            return expiry
            
        except Exception as e:
            logger.error(f"Error parsing expiry time: {str(e)}")
            return None
    
    def validate_signal(self, signal: TradingSignal) -> bool:
        """Validate a parsed signal"""
        try:
            # Check if asset is allowed
            if signal.asset not in settings.allowed_assets:
                logger.warning(f"Asset {signal.asset} not in allowed assets")
                return False
            
            # Check amount limits
            if signal.amount < settings.min_trade_amount or signal.amount > settings.max_trade_amount:
                logger.warning(f"Amount {signal.amount} outside allowed range")
                return False
            
            # Check duration limits (1 minute to 1 hour)
            if signal.duration < 60 or signal.duration > 3600:
                logger.warning(f"Duration {signal.duration}s outside allowed range")
                return False
            
            # Check confidence if provided
            if signal.confidence and signal.confidence < settings.min_signal_confidence:
                logger.warning(f"Signal confidence {signal.confidence}% below minimum {settings.min_signal_confidence}%")
                return False
            
            # Check if signal is not expired
            if signal.expiry_time and signal.expiry_time <= datetime.now(pytz.UTC):
                logger.warning("Signal has expired")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return False
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """Get statistics about signal parsing"""
        # This could be expanded to track parsing success rates, etc.
        return {
            'patterns_count': len(self.signal_patterns),
            'allowed_assets': settings.allowed_assets,
            'min_confidence': settings.min_signal_confidence
        }