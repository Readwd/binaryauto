"""
QXBroker client for handling trading operations
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time

try:
    from quotexpy import Quotex
except ImportError:
    print("Warning: quotexpy not installed. Please install it with: pip install quotexpy")
    Quotex = None

from config import settings, ASSET_MAPPING
from core.models import Trade, TradeDirection, TradeStatus, BrokerConnection

logger = logging.getLogger(__name__)

class QXBrokerClient:
    """QXBroker client for trading operations"""
    
    def __init__(self):
        self.client: Optional[Quotex] = None
        self.connection_status = BrokerConnection()
        self.active_trades: Dict[str, Trade] = {}
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    async def connect(self) -> bool:
        """Connect to QXBroker"""
        try:
            if not Quotex:
                raise ImportError("quotexpy library not available")
                
            logger.info("Connecting to QXBroker...")
            
            # Initialize client based on host
            if settings.qxbroker_host == "quotex.com":
                # For Quotex.com, we need SSID authentication
                # This would require manual SSID extraction
                logger.warning("Quotex.com requires SSID authentication. Please provide SSID in environment variables.")
                return False
            else:
                # For QXBroker, use email/password
                self.client = Quotex(
                    email=settings.qxbroker_email,
                    password=settings.qxbroker_password
                )
            
            # Attempt connection
            check_connect, message = await asyncio.to_thread(self.client.connect)
            
            if check_connect:
                logger.info("Successfully connected to QXBroker")
                
                # Set account mode
                await asyncio.to_thread(
                    self.client.change_balance, 
                    settings.qxbroker_mode
                )
                
                # Get initial balance
                balance = await asyncio.to_thread(self.client.get_balance)
                
                self.connection_status.update_connection_status(True)
                self.connection_status.balance = balance
                self.connection_status.account_type = settings.qxbroker_mode
                
                logger.info(f"Account mode: {settings.qxbroker_mode}, Balance: {balance}")
                self.reconnect_attempts = 0
                
                return True
            else:
                error_msg = f"Failed to connect: {message}"
                logger.error(error_msg)
                self.connection_status.update_connection_status(False, error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            self.connection_status.update_connection_status(False, error_msg)
            return False
    
    async def disconnect(self):
        """Disconnect from QXBroker"""
        try:
            if self.client:
                await asyncio.to_thread(self.client.close)
                logger.info("Disconnected from QXBroker")
            
            self.connection_status.update_connection_status(False)
            self.client = None
            
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect to QXBroker"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Maximum reconnection attempts reached")
            return False
        
        self.reconnect_attempts += 1
        logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        await self.disconnect()
        await asyncio.sleep(5)  # Wait before reconnecting
        
        return await self.connect()
    
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self.connection_status.is_connected and self.client is not None
    
    async def get_balance(self) -> Optional[float]:
        """Get account balance"""
        try:
            if not self.is_connected():
                logger.warning("Not connected to broker")
                return None
            
            balance = await asyncio.to_thread(self.client.get_balance)
            self.connection_status.balance = balance
            return balance
            
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return None
    
    def _get_broker_asset_name(self, asset: str) -> str:
        """Convert asset name to broker-specific format"""
        asset_mapping = ASSET_MAPPING.get(settings.qxbroker_host, {})
        return asset_mapping.get(asset, asset)
    
    async def place_trade(self, trade: Trade) -> bool:
        """Place a trade on QXBroker"""
        try:
            if not self.is_connected():
                logger.warning("Not connected to broker")
                return False
            
            broker_asset = self._get_broker_asset_name(trade.asset)
            direction = trade.direction.value
            
            logger.info(f"Placing trade: {broker_asset} {direction} ${trade.amount} {trade.duration}s")
            
            # Place the trade
            result = await asyncio.to_thread(
                self.client.buy,
                broker_asset,
                trade.amount,
                direction,
                trade.duration
            )
            
            if result and isinstance(result, dict) and result.get('id'):
                trade.broker_trade_id = str(result['id'])
                trade.status = TradeStatus.ACTIVE
                trade.entry_price = result.get('price')
                
                # Store active trade
                self.active_trades[trade.id] = trade
                
                logger.info(f"Trade placed successfully: {trade.broker_trade_id}")
                return True
            else:
                logger.error(f"Failed to place trade: {result}")
                trade.status = TradeStatus.ERROR
                return False
                
        except Exception as e:
            error_msg = f"Error placing trade: {str(e)}"
            logger.error(error_msg)
            trade.status = TradeStatus.ERROR
            trade.metadata['error'] = error_msg
            return False
    
    async def check_trade_result(self, trade: Trade) -> Optional[TradeStatus]:
        """Check the result of a trade"""
        try:
            if not self.is_connected() or not trade.broker_trade_id:
                return None
            
            # Check trade result
            result = await asyncio.to_thread(
                self.client.check_win,
                trade.broker_trade_id
            )
            
            if result is not None:
                if result > 0:
                    trade.status = TradeStatus.WON
                    trade.profit_loss = result
                    trade.end_time = datetime.now()
                    logger.info(f"Trade {trade.id} WON: ${result}")
                else:
                    trade.status = TradeStatus.LOST
                    trade.profit_loss = -trade.amount
                    trade.end_time = datetime.now()
                    logger.info(f"Trade {trade.id} LOST: ${trade.amount}")
                
                # Remove from active trades
                if trade.id in self.active_trades:
                    del self.active_trades[trade.id]
                
                return trade.status
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking trade result: {str(e)}")
            return None
    
    async def get_candles(self, asset: str, timeframe: int = 60, count: int = 100) -> Optional[List[Dict]]:
        """Get historical candle data"""
        try:
            if not self.is_connected():
                return None
            
            broker_asset = self._get_broker_asset_name(asset)
            
            # Get current time and calculate offset
            current_time = int(time.time())
            offset = timeframe * count
            
            candles = await asyncio.to_thread(
                self.client.get_candle,
                broker_asset,
                current_time,
                offset,
                timeframe
            )
            
            if candles and 'data' in candles:
                return candles['data']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting candles: {str(e)}")
            return None
    
    async def check_asset_open(self, asset: str) -> bool:
        """Check if asset is open for trading"""
        try:
            if not self.is_connected():
                return False
            
            broker_asset = self._get_broker_asset_name(asset)
            
            is_open = await asyncio.to_thread(
                self.client.check_asset_open,
                broker_asset
            )
            
            return bool(is_open)
            
        except Exception as e:
            logger.error(f"Error checking asset status: {str(e)}")
            return False
    
    async def get_payout(self, asset: str) -> Optional[float]:
        """Get payout percentage for asset"""
        try:
            if not self.is_connected():
                return None
            
            broker_asset = self._get_broker_asset_name(asset)
            
            payment_data = await asyncio.to_thread(self.client.get_payment)
            
            if payment_data and broker_asset in payment_data:
                return payment_data[broker_asset].get('payment', 0.0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting payout: {str(e)}")
            return None
    
    async def monitor_active_trades(self):
        """Monitor active trades for results"""
        while True:
            try:
                if not self.is_connected():
                    await asyncio.sleep(5)
                    continue
                
                # Check each active trade
                trades_to_check = list(self.active_trades.values())
                
                for trade in trades_to_check:
                    # Check if trade duration has passed
                    if trade.start_time:
                        elapsed = (datetime.now() - trade.start_time).total_seconds()
                        if elapsed >= trade.duration:
                            await self.check_trade_result(trade)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error monitoring trades: {str(e)}")
                await asyncio.sleep(5)
    
    async def health_check(self):
        """Perform health check and reconnect if needed"""
        while True:
            try:
                if not self.is_connected():
                    logger.warning("Connection lost, attempting to reconnect...")
                    await self.reconnect()
                else:
                    # Update balance
                    await self.get_balance()
                
                await asyncio.sleep(30)  # Health check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                await asyncio.sleep(30)
    
    def get_connection_status(self) -> BrokerConnection:
        """Get current connection status"""
        return self.connection_status
    
    def get_active_trades_count(self) -> int:
        """Get number of active trades"""
        return len(self.active_trades)
    
    async def cancel_all_trades(self):
        """Cancel all active trades (if supported)"""
        try:
            if not self.is_connected():
                return
            
            for trade in list(self.active_trades.values()):
                trade.status = TradeStatus.CANCELLED
                trade.end_time = datetime.now()
            
            self.active_trades.clear()
            logger.info("All active trades cancelled")
            
        except Exception as e:
            logger.error(f"Error cancelling trades: {str(e)}")