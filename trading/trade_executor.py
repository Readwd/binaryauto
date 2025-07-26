"""
Trade execution engine for QXBroker Auto Trading Bot
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
import queue
import threading

from config import settings
from core.models import (
    TradingSignal, Trade, TradeStatus, TradeDirection,
    SignalSource, MartingaleSequence
)
from brokers import QXBrokerClient
from .risk_manager import RiskManager

logger = logging.getLogger(__name__)

class TradeExecutor:
    """Main trade execution engine"""
    
    def __init__(self, broker_client: QXBrokerClient, risk_manager: RiskManager):
        self.broker = broker_client
        self.risk_manager = risk_manager
        self.signal_queue = asyncio.Queue()
        self.active_trades: Dict[str, Trade] = {}
        self.pending_signals: Dict[str, TradingSignal] = {}
        
        # Callbacks
        self.trade_callback: Optional[Callable[[Trade], None]] = None
        self.signal_callback: Optional[Callable[[TradingSignal, str], None]] = None
        
        # Control flags
        self.is_running = False
        self.auto_trading_enabled = True
        
        # Statistics
        self.signals_received = 0
        self.trades_executed = 0
        self.trades_won = 0
        self.trades_lost = 0
        
    async def start(self):
        """Start the trade executor"""
        if self.is_running:
            logger.warning("Trade executor is already running")
            return
        
        logger.info("Starting trade executor...")
        self.is_running = True
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._process_signals()),
            asyncio.create_task(self._monitor_trades()),
            asyncio.create_task(self._process_pending_signals()),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in trade executor: {str(e)}")
        finally:
            self.is_running = False
    
    async def stop(self):
        """Stop the trade executor"""
        logger.info("Stopping trade executor...")
        self.is_running = False
        
        # Cancel all pending signals
        self.pending_signals.clear()
        
        # Wait for active trades to complete (optional)
        if self.active_trades:
            logger.info(f"Waiting for {len(self.active_trades)} active trades to complete...")
            # In a real implementation, you might want to wait or force close
    
    async def add_signal(self, signal: TradingSignal):
        """Add a trading signal to the queue"""
        try:
            await self.signal_queue.put(signal)
            self.signals_received += 1
            logger.debug(f"Added signal to queue: {signal.asset} {signal.direction}")
            
        except Exception as e:
            logger.error(f"Error adding signal to queue: {str(e)}")
    
    async def _process_signals(self):
        """Process trading signals from the queue"""
        while self.is_running:
            try:
                # Wait for signal with timeout
                try:
                    signal = await asyncio.wait_for(self.signal_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                logger.info(f"Processing signal: {signal.asset} {signal.direction} ${signal.amount}")
                
                # Check if auto trading is enabled
                if not self.auto_trading_enabled:
                    logger.info("Auto trading disabled, skipping signal")
                    if self.signal_callback:
                        await self._call_signal_callback(signal, "Auto trading disabled")
                    continue
                
                # Check if signal has expiry time
                if signal.expiry_time and signal.expiry_time > datetime.now():
                    logger.info(f"Signal scheduled for {signal.expiry_time}, adding to pending")
                    self.pending_signals[signal.id] = signal
                    continue
                
                # Process signal immediately
                await self._execute_signal(signal)
                
            except Exception as e:
                logger.error(f"Error processing signal: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_pending_signals(self):
        """Process signals that are scheduled for future execution"""
        while self.is_running:
            try:
                current_time = datetime.now()
                signals_to_execute = []
                
                # Check for signals ready to execute
                for signal_id, signal in list(self.pending_signals.items()):
                    if signal.expiry_time and signal.expiry_time <= current_time:
                        signals_to_execute.append(signal)
                        del self.pending_signals[signal_id]
                
                # Execute ready signals
                for signal in signals_to_execute:
                    logger.info(f"Executing scheduled signal: {signal.asset} {signal.direction}")
                    await self._execute_signal(signal)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error processing pending signals: {str(e)}")
                await asyncio.sleep(5)
    
    async def _execute_signal(self, signal: TradingSignal):
        """Execute a trading signal"""
        try:
            # Get current balance
            current_balance = await self.broker.get_balance()
            if current_balance is None:
                logger.error("Could not get current balance")
                if self.signal_callback:
                    await self._call_signal_callback(signal, "Could not get balance")
                return
            
            # Check risk management
            can_trade, reason = await self.risk_manager.can_place_trade(signal, current_balance)
            if not can_trade:
                logger.warning(f"Trade rejected by risk manager: {reason}")
                if self.signal_callback:
                    await self._call_signal_callback(signal, f"Risk check failed: {reason}")
                return
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(signal, current_balance)
            
            # Update signal amount if different
            if position_size != signal.amount:
                logger.info(f"Position size adjusted from ${signal.amount} to ${position_size}")
                signal.amount = position_size
            
            # Check if asset is open for trading
            if not await self.broker.check_asset_open(signal.asset):
                logger.warning(f"Asset {signal.asset} is not open for trading")
                if self.signal_callback:
                    await self._call_signal_callback(signal, "Asset not open for trading")
                return
            
            # Create trade object
            trade = Trade(
                signal_id=signal.id,
                asset=signal.asset,
                direction=signal.direction,
                amount=signal.amount,
                duration=signal.duration
            )
            
            # Place the trade
            success = await self.broker.place_trade(trade)
            
            if success:
                # Add to active trades
                self.active_trades[trade.id] = trade
                self.trades_executed += 1
                
                # Update risk manager
                self.risk_manager.update_concurrent_trades(len(self.active_trades))
                
                logger.info(f"Trade placed successfully: {trade.id}")
                
                if self.trade_callback:
                    await self._call_trade_callback(trade)
                
                if self.signal_callback:
                    await self._call_signal_callback(signal, "Trade placed successfully")
            else:
                logger.error(f"Failed to place trade for signal {signal.id}")
                if self.signal_callback:
                    await self._call_signal_callback(signal, "Failed to place trade")
                
        except Exception as e:
            logger.error(f"Error executing signal: {str(e)}")
            if self.signal_callback:
                await self._call_signal_callback(signal, f"Execution error: {str(e)}")
    
    async def _monitor_trades(self):
        """Monitor active trades for completion"""
        while self.is_running:
            try:
                if not self.active_trades:
                    await asyncio.sleep(1)
                    continue
                
                # Check each active trade
                completed_trades = []
                
                for trade_id, trade in list(self.active_trades.items()):
                    # Check if trade duration has passed
                    if trade.start_time:
                        elapsed = (datetime.now() - trade.start_time).total_seconds()
                        if elapsed >= trade.duration + 10:  # Add 10 seconds buffer
                            # Check trade result
                            result = await self.broker.check_trade_result(trade)
                            
                            if result:
                                completed_trades.append(trade)
                                
                                # Update statistics
                                if trade.status == TradeStatus.WON:
                                    self.trades_won += 1
                                elif trade.status == TradeStatus.LOST:
                                    self.trades_lost += 1
                                
                                # Record result in risk manager
                                self.risk_manager.record_trade_result(trade)
                                
                                logger.info(f"Trade completed: {trade.id} - {trade.status.value}")
                                
                                # Call trade callback
                                if self.trade_callback:
                                    await self._call_trade_callback(trade)
                                
                                # Check for martingale opportunity
                                if trade.status == TradeStatus.LOST:
                                    await self._handle_martingale(trade)
                
                # Remove completed trades
                for trade in completed_trades:
                    if trade.id in self.active_trades:
                        del self.active_trades[trade.id]
                
                # Update concurrent trades count
                self.risk_manager.update_concurrent_trades(len(self.active_trades))
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error monitoring trades: {str(e)}")
                await asyncio.sleep(5)
    
    async def _handle_martingale(self, lost_trade: Trade):
        """Handle martingale strategy for lost trades"""
        try:
            if not self.risk_manager.should_use_martingale(lost_trade.signal_id):
                logger.debug(f"Martingale not applicable for trade {lost_trade.id}")
                return
            
            # Get current balance
            current_balance = await self.broker.get_balance()
            if current_balance is None:
                logger.error("Could not get balance for martingale")
                return
            
            # Get or create martingale sequence
            sequence = self.risk_manager.martingale_sequences.get(lost_trade.signal_id)
            if not sequence:
                # Create new sequence using original signal
                original_signal = TradingSignal(
                    asset=lost_trade.asset,
                    direction=lost_trade.direction,
                    amount=lost_trade.amount,
                    duration=lost_trade.duration,
                    source=SignalSource.TELEGRAM
                )
                sequence = self.risk_manager.create_martingale_sequence(original_signal)
            
            # Get next martingale amount
            next_amount = self.risk_manager.get_next_martingale_amount(
                lost_trade.signal_id, 
                current_balance
            )
            
            if not next_amount:
                logger.warning(f"Cannot continue martingale for trade {lost_trade.id}")
                return
            
            # Create martingale signal
            martingale_signal = TradingSignal(
                asset=lost_trade.asset,
                direction=lost_trade.direction,
                amount=next_amount,
                duration=lost_trade.duration,
                source=SignalSource.TELEGRAM,
                metadata={
                    'martingale_sequence_id': sequence.sequence_id,
                    'martingale_step': sequence.current_step + 1,
                    'original_signal_id': lost_trade.signal_id
                }
            )
            
            logger.info(f"Creating martingale trade: Step {sequence.current_step + 1}, Amount ${next_amount}")
            
            # Add to queue for processing
            await self.add_signal(martingale_signal)
            
        except Exception as e:
            logger.error(f"Error handling martingale: {str(e)}")
    
    async def _call_trade_callback(self, trade: Trade):
        """Call the trade callback function"""
        try:
            if self.trade_callback:
                if asyncio.iscoroutinefunction(self.trade_callback):
                    await self.trade_callback(trade)
                else:
                    self.trade_callback(trade)
        except Exception as e:
            logger.error(f"Error in trade callback: {str(e)}")
    
    async def _call_signal_callback(self, signal: TradingSignal, message: str):
        """Call the signal callback function"""
        try:
            if self.signal_callback:
                if asyncio.iscoroutinefunction(self.signal_callback):
                    await self.signal_callback(signal, message)
                else:
                    self.signal_callback(signal, message)
        except Exception as e:
            logger.error(f"Error in signal callback: {str(e)}")
    
    def set_trade_callback(self, callback: Callable[[Trade], None]):
        """Set the trade callback function"""
        self.trade_callback = callback
    
    def set_signal_callback(self, callback: Callable[[TradingSignal, str], None]):
        """Set the signal callback function"""
        self.signal_callback = callback
    
    def enable_auto_trading(self):
        """Enable automatic trading"""
        self.auto_trading_enabled = True
        logger.info("Auto trading enabled")
    
    def disable_auto_trading(self):
        """Disable automatic trading"""
        self.auto_trading_enabled = False
        logger.info("Auto trading disabled")
    
    async def cancel_all_trades(self):
        """Cancel all active trades"""
        try:
            logger.info("Cancelling all active trades...")
            
            # Cancel trades on broker
            await self.broker.cancel_all_trades()
            
            # Update local trades
            for trade in self.active_trades.values():
                trade.status = TradeStatus.CANCELLED
                trade.end_time = datetime.now()
                
                # Record in risk manager
                self.risk_manager.record_trade_result(trade)
            
            # Clear active trades
            self.active_trades.clear()
            
            # Update concurrent trades count
            self.risk_manager.update_concurrent_trades(0)
            
            logger.info("All trades cancelled")
            
        except Exception as e:
            logger.error(f"Error cancelling trades: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics"""
        win_rate = 0.0
        if self.trades_executed > 0:
            win_rate = (self.trades_won / self.trades_executed) * 100
        
        return {
            'is_running': self.is_running,
            'auto_trading_enabled': self.auto_trading_enabled,
            'signals_received': self.signals_received,
            'trades_executed': self.trades_executed,
            'trades_won': self.trades_won,
            'trades_lost': self.trades_lost,
            'win_rate': win_rate,
            'active_trades': len(self.active_trades),
            'pending_signals': len(self.pending_signals),
            'risk_summary': self.risk_manager.get_risk_summary()
        }
    
    def get_active_trades(self) -> List[Dict[str, Any]]:
        """Get list of active trades"""
        return [
            {
                'id': trade.id,
                'asset': trade.asset,
                'direction': trade.direction.value,
                'amount': trade.amount,
                'duration': trade.duration,
                'start_time': trade.start_time.isoformat() if trade.start_time else None,
                'status': trade.status.value
            }
            for trade in self.active_trades.values()
        ]
    
    def get_pending_signals(self) -> List[Dict[str, Any]]:
        """Get list of pending signals"""
        return [
            {
                'id': signal.id,
                'asset': signal.asset,
                'direction': signal.direction.value,
                'amount': signal.amount,
                'duration': signal.duration,
                'expiry_time': signal.expiry_time.isoformat() if signal.expiry_time else None
            }
            for signal in self.pending_signals.values()
        ]