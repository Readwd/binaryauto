"""
Telegram client for receiving and processing trading signals
"""
import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime

try:
    from telethon import TelegramClient, events
    from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
except ImportError:
    print("Warning: telethon not installed. Please install it with: pip install telethon")
    TelegramClient = None
    events = None

from config import settings
from core.models import TelegramMessage, TradingSignal, SignalSource
from .signal_parser import TelegramSignalParser

logger = logging.getLogger(__name__)

class TelegramSignalClient:
    """Telegram client for receiving trading signals"""
    
    def __init__(self, signal_callback: Optional[Callable[[TradingSignal], None]] = None):
        self.client: Optional[TelegramClient] = None
        self.signal_parser = TelegramSignalParser()
        self.signal_callback = signal_callback
        self.is_connected = False
        self.monitored_chats = set()
        
        # Statistics
        self.messages_received = 0
        self.signals_parsed = 0
        self.signals_sent = 0
        
    async def connect(self) -> bool:
        """Connect to Telegram"""
        try:
            if not TelegramClient:
                raise ImportError("telethon library not available")
            
            if not settings.telegram_api_id or not settings.telegram_api_hash:
                logger.error("Telegram API credentials not configured")
                return False
            
            logger.info("Connecting to Telegram...")
            
            # Create client
            self.client = TelegramClient(
                'trading_bot_session',
                settings.telegram_api_id,
                settings.telegram_api_hash
            )
            
            # Connect
            await self.client.connect()
            
            # Check if we're authorized
            if not await self.client.is_user_authorized():
                logger.info("Not authorized, requesting phone code...")
                
                if not settings.telegram_phone_number:
                    logger.error("Phone number not configured")
                    return False
                
                # Send code request
                await self.client.send_code_request(settings.telegram_phone_number)
                
                # In a real implementation, you'd need to handle code input
                logger.warning("Please check your Telegram for the verification code and update your session")
                return False
            
            # Get current user info
            me = await self.client.get_me()
            logger.info(f"Connected to Telegram as {me.first_name} (@{me.username})")
            
            # Set up event handlers
            self._setup_event_handlers()
            
            # Add monitored chats
            if settings.telegram_chat_id:
                await self.add_monitored_chat(settings.telegram_chat_id)
            
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Telegram: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        try:
            if self.client:
                await self.client.disconnect()
                logger.info("Disconnected from Telegram")
            
            self.is_connected = False
            
        except Exception as e:
            logger.error(f"Error disconnecting from Telegram: {str(e)}")
    
    def _setup_event_handlers(self):
        """Set up Telegram event handlers"""
        if not self.client:
            return
        
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            """Handle new Telegram messages"""
            try:
                await self._process_message(event)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
        
        @self.client.on(events.MessageEdited)
        async def handle_edited_message(event):
            """Handle edited Telegram messages"""
            try:
                await self._process_message(event, is_edited=True)
            except Exception as e:
                logger.error(f"Error processing edited message: {str(e)}")
    
    async def _process_message(self, event, is_edited: bool = False):
        """Process a Telegram message"""
        try:
            message = event.message
            
            # Skip if not from monitored chats
            if self.monitored_chats and str(message.chat_id) not in self.monitored_chats:
                return
            
            # Skip empty messages
            if not message.text:
                return
            
            self.messages_received += 1
            
            # Create TelegramMessage object
            telegram_msg = TelegramMessage(
                message_id=message.id,
                chat_id=message.chat_id,
                user_id=message.from_id.user_id if message.from_id else None,
                username=event.sender.username if event.sender else None,
                text=message.text,
                timestamp=message.date
            )
            
            logger.debug(f"Processing {'edited ' if is_edited else ''}message from {telegram_msg.username}: {telegram_msg.text[:100]}...")
            
            # Try to parse as trading signal
            signal = self.signal_parser.parse_message(telegram_msg.text)
            
            if signal:
                # Validate signal
                if self.signal_parser.validate_signal(signal):
                    telegram_msg.is_signal = True
                    telegram_msg.parsed_signal = signal
                    self.signals_parsed += 1
                    
                    logger.info(f"Valid signal parsed: {signal.asset} {signal.direction} ${signal.amount} {signal.duration}s")
                    
                    # Call signal callback if provided
                    if self.signal_callback:
                        try:
                            await self._call_signal_callback(signal)
                            self.signals_sent += 1
                        except Exception as e:
                            logger.error(f"Error in signal callback: {str(e)}")
                else:
                    logger.debug("Signal validation failed")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    async def _call_signal_callback(self, signal: TradingSignal):
        """Call the signal callback function"""
        if self.signal_callback:
            if asyncio.iscoroutinefunction(self.signal_callback):
                await self.signal_callback(signal)
            else:
                self.signal_callback(signal)
    
    async def add_monitored_chat(self, chat_identifier: str):
        """Add a chat to monitor for signals"""
        try:
            if not self.client:
                logger.error("Not connected to Telegram")
                return False
            
            # Try to get chat entity
            try:
                chat = await self.client.get_entity(chat_identifier)
                chat_id = str(chat.id)
                self.monitored_chats.add(chat_id)
                
                logger.info(f"Added chat to monitoring: {chat.title if hasattr(chat, 'title') else chat_identifier}")
                return True
                
            except Exception as e:
                logger.error(f"Error adding chat {chat_identifier}: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding monitored chat: {str(e)}")
            return False
    
    async def remove_monitored_chat(self, chat_identifier: str):
        """Remove a chat from monitoring"""
        try:
            if chat_identifier in self.monitored_chats:
                self.monitored_chats.remove(chat_identifier)
                logger.info(f"Removed chat from monitoring: {chat_identifier}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing monitored chat: {str(e)}")
            return False
    
    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a Telegram chat"""
        try:
            if not self.client or not self.is_connected:
                logger.error("Not connected to Telegram")
                return False
            
            await self.client.send_message(chat_id, message)
            logger.debug(f"Message sent to {chat_id}: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    async def send_trade_notification(self, chat_id: str, signal: TradingSignal, trade_result: Optional[str] = None):
        """Send a trade notification to Telegram"""
        try:
            if trade_result:
                message = f"🔔 Trade Result\n"
                message += f"Asset: {signal.asset}\n"
                message += f"Direction: {signal.direction.value.upper()}\n"
                message += f"Amount: ${signal.amount}\n"
                message += f"Result: {trade_result}\n"
                message += f"Time: {datetime.now().strftime('%H:%M:%S')}"
            else:
                message = f"📊 Trade Signal Received\n"
                message += f"Asset: {signal.asset}\n"
                message += f"Direction: {signal.direction.value.upper()}\n"
                message += f"Amount: ${signal.amount}\n"
                message += f"Duration: {signal.duration}s\n"
                if signal.confidence:
                    message += f"Confidence: {signal.confidence}%\n"
                message += f"Time: {signal.timestamp.strftime('%H:%M:%S')}"
            
            return await self.send_message(chat_id, message)
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {str(e)}")
            return False
    
    async def get_chat_history(self, chat_id: str, limit: int = 100) -> list:
        """Get recent messages from a chat"""
        try:
            if not self.client or not self.is_connected:
                logger.error("Not connected to Telegram")
                return []
            
            messages = []
            async for message in self.client.iter_messages(chat_id, limit=limit):
                if message.text:
                    messages.append({
                        'id': message.id,
                        'text': message.text,
                        'date': message.date,
                        'sender': message.sender.username if message.sender else None
                    })
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return []
    
    async def run_until_disconnected(self):
        """Run the client until disconnected"""
        try:
            if self.client:
                logger.info("Telegram client running... Press Ctrl+C to stop")
                await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Telegram client stopped by user")
        except Exception as e:
            logger.error(f"Error running Telegram client: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            'is_connected': self.is_connected,
            'monitored_chats': len(self.monitored_chats),
            'messages_received': self.messages_received,
            'signals_parsed': self.signals_parsed,
            'signals_sent': self.signals_sent,
            'parser_stats': self.signal_parser.get_signal_statistics()
        }
    
    def set_signal_callback(self, callback: Callable[[TradingSignal], None]):
        """Set the signal callback function"""
        self.signal_callback = callback
    
    async def test_signal_parsing(self, test_messages: list) -> Dict[str, Any]:
        """Test signal parsing with sample messages"""
        results = {
            'total_messages': len(test_messages),
            'parsed_signals': 0,
            'valid_signals': 0,
            'results': []
        }
        
        for message in test_messages:
            signal = self.signal_parser.parse_message(message)
            is_valid = False
            
            if signal:
                results['parsed_signals'] += 1
                is_valid = self.signal_parser.validate_signal(signal)
                if is_valid:
                    results['valid_signals'] += 1
            
            results['results'].append({
                'message': message,
                'parsed': signal is not None,
                'valid': is_valid,
                'signal': signal.dict() if signal else None
            })
        
        return results