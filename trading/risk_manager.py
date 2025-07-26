"""
Risk management system for QXBroker Auto Trading Bot
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio

from config import settings
from core.models import (
    Trade, TradingSignal, TradeStatus, RiskMetrics, 
    MartingaleSequence, TradingSession
)

logger = logging.getLogger(__name__)

class RiskManager:
    """Risk management system for trading operations"""
    
    def __init__(self):
        self.risk_metrics = RiskMetrics()
        self.current_session: Optional[TradingSession] = None
        self.martingale_sequences: Dict[str, MartingaleSequence] = {}
        self.daily_reset_time = None
        self._last_daily_reset = datetime.now().date()
        
    def start_session(self, initial_balance: float) -> TradingSession:
        """Start a new trading session"""
        if self.current_session and self.current_session.is_active:
            logger.warning("Ending previous active session")
            self.end_session()
        
        self.current_session = TradingSession(
            balance_start=initial_balance
        )
        
        logger.info(f"Started new trading session: {self.current_session.id}")
        return self.current_session
    
    def end_session(self, final_balance: Optional[float] = None):
        """End the current trading session"""
        if not self.current_session:
            logger.warning("No active session to end")
            return
        
        self.current_session.end_time = datetime.now()
        if final_balance is not None:
            self.current_session.balance_end = final_balance
        
        logger.info(f"Ended trading session: {self.current_session.id}")
        logger.info(f"Session stats - Trades: {self.current_session.total_trades}, "
                   f"Win rate: {self.current_session.win_rate:.1f}%, "
                   f"P&L: {self.current_session.total_profit_loss:.2f}")
    
    async def can_place_trade(self, signal: TradingSignal, current_balance: float) -> tuple[bool, str]:
        """Check if a trade can be placed based on risk management rules"""
        try:
            # Check daily reset
            await self._check_daily_reset()
            
            # Check if trading is allowed
            if not self._is_trading_allowed():
                return False, "Trading is currently disabled"
            
            # Check concurrent trades limit
            if self.risk_metrics.concurrent_trades >= settings.max_concurrent_trades:
                return False, f"Maximum concurrent trades limit reached ({settings.max_concurrent_trades})"
            
            # Check daily loss limit
            if self.risk_metrics.daily_loss >= settings.max_daily_loss:
                return False, f"Daily loss limit reached (${settings.max_daily_loss})"
            
            # Check balance requirements
            min_balance_required = signal.amount * 2  # Keep at least 2x trade amount
            if current_balance < min_balance_required:
                return False, f"Insufficient balance. Required: ${min_balance_required}, Available: ${current_balance}"
            
            # Check risk percentage
            risk_amount = (current_balance * settings.risk_percentage) / 100
            if signal.amount > risk_amount:
                return False, f"Trade amount ${signal.amount} exceeds risk limit ${risk_amount:.2f} ({settings.risk_percentage}% of balance)"
            
            # Check consecutive losses
            if self.risk_metrics.consecutive_losses >= 5:  # Hardcoded limit
                return False, "Too many consecutive losses. Trading paused for safety."
            
            # Check time-based restrictions (market hours, etc.)
            if not self._is_market_hours():
                return False, "Outside of allowed trading hours"
            
            return True, "Trade approved"
            
        except Exception as e:
            logger.error(f"Error checking trade approval: {str(e)}")
            return False, f"Risk check error: {str(e)}"
    
    def calculate_position_size(self, signal: TradingSignal, current_balance: float) -> float:
        """Calculate optimal position size based on risk management"""
        try:
            # Base amount from signal
            base_amount = signal.amount
            
            # Apply risk percentage limit
            max_risk_amount = (current_balance * settings.risk_percentage) / 100
            
            # Apply min/max limits
            min_amount = settings.min_trade_amount
            max_amount = min(settings.max_trade_amount, max_risk_amount)
            
            # Adjust for consecutive losses (reduce position size)
            if self.risk_metrics.consecutive_losses > 0:
                reduction_factor = 0.9 ** self.risk_metrics.consecutive_losses
                base_amount *= reduction_factor
                logger.debug(f"Reduced position size by {(1-reduction_factor)*100:.1f}% due to consecutive losses")
            
            # Ensure within limits
            position_size = max(min_amount, min(base_amount, max_amount))
            
            logger.debug(f"Calculated position size: ${position_size:.2f} (original: ${signal.amount})")
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return settings.min_trade_amount
    
    def should_use_martingale(self, original_signal_id: str) -> bool:
        """Check if martingale should be used for a failed trade"""
        if not settings.martingale_enabled:
            return False
        
        # Check if we already have a martingale sequence for this signal
        sequence = self.martingale_sequences.get(original_signal_id)
        if sequence and sequence.current_step >= settings.max_martingale_steps:
            return False
        
        # Check consecutive losses
        if self.risk_metrics.consecutive_losses < 1:
            return False
        
        return True
    
    def create_martingale_sequence(self, original_signal: TradingSignal) -> MartingaleSequence:
        """Create a new martingale sequence"""
        sequence = MartingaleSequence(
            original_signal_id=original_signal.id,
            base_amount=original_signal.amount,
            max_steps=settings.max_martingale_steps
        )
        
        self.martingale_sequences[original_signal.id] = sequence
        logger.info(f"Created martingale sequence for signal {original_signal.id}")
        
        return sequence
    
    def get_next_martingale_amount(self, original_signal_id: str, current_balance: float) -> Optional[float]:
        """Get the next martingale amount"""
        sequence = self.martingale_sequences.get(original_signal_id)
        if not sequence:
            return None
        
        try:
            next_amount = sequence.next_step(settings.martingale_multiplier)
            
            # Check if we can afford this amount
            if next_amount > current_balance * 0.5:  # Don't risk more than 50% of balance
                logger.warning(f"Martingale amount ${next_amount} too large for balance ${current_balance}")
                return None
            
            return next_amount
            
        except ValueError as e:
            logger.warning(f"Cannot continue martingale sequence: {str(e)}")
            return None
    
    def record_trade_result(self, trade: Trade):
        """Record the result of a trade for risk metrics"""
        try:
            # Update session stats
            if self.current_session:
                self.current_session.total_trades += 1
                
                if trade.status == TradeStatus.WON:
                    self.current_session.winning_trades += 1
                    self.current_session.total_profit_loss += (trade.profit_loss or 0)
                    
                    # Update risk metrics
                    self.risk_metrics.daily_profit += (trade.profit_loss or 0)
                    self.risk_metrics.consecutive_losses = 0
                    
                elif trade.status == TradeStatus.LOST:
                    self.current_session.losing_trades += 1
                    self.current_session.total_profit_loss -= trade.amount
                    
                    # Update risk metrics
                    self.risk_metrics.daily_loss += trade.amount
                    self.risk_metrics.consecutive_losses += 1
                    self.risk_metrics.max_consecutive_losses = max(
                        self.risk_metrics.max_consecutive_losses,
                        self.risk_metrics.consecutive_losses
                    )
            
            # Update martingale sequences
            self._update_martingale_sequences(trade)
            
            # Update last trade time
            self.risk_metrics.last_trade_time = datetime.now()
            
            logger.debug(f"Recorded trade result: {trade.status.value} for ${trade.amount}")
            
        except Exception as e:
            logger.error(f"Error recording trade result: {str(e)}")
    
    def _update_martingale_sequences(self, trade: Trade):
        """Update martingale sequences based on trade result"""
        try:
            # Find if this trade belongs to a martingale sequence
            for sequence in self.martingale_sequences.values():
                if trade.id in sequence.trades:
                    sequence.add_trade(trade.id, trade.amount)
                    
                    if trade.status == TradeStatus.WON:
                        sequence.complete_sequence(TradeStatus.WON)
                        logger.info(f"Martingale sequence {sequence.sequence_id} completed successfully")
                    elif trade.status == TradeStatus.LOST and sequence.current_step >= sequence.max_steps:
                        sequence.complete_sequence(TradeStatus.LOST)
                        logger.warning(f"Martingale sequence {sequence.sequence_id} failed after {sequence.max_steps} steps")
                    
                    break
                    
        except Exception as e:
            logger.error(f"Error updating martingale sequences: {str(e)}")
    
    def update_concurrent_trades(self, count: int):
        """Update the count of concurrent trades"""
        self.risk_metrics.concurrent_trades = count
    
    async def _check_daily_reset(self):
        """Check if daily metrics should be reset"""
        current_date = datetime.now().date()
        
        if current_date > self._last_daily_reset:
            logger.info("Performing daily risk metrics reset")
            self.risk_metrics.reset_daily_metrics()
            self._last_daily_reset = current_date
    
    def _is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed"""
        # Check if we're in a safe state to trade
        if self.risk_metrics.consecutive_losses >= 10:  # Emergency stop
            return False
        
        if self.risk_metrics.daily_loss >= settings.max_daily_loss:
            return False
        
        return True
    
    def _is_market_hours(self) -> bool:
        """Check if we're within allowed trading hours"""
        # For forex markets, this could be more sophisticated
        # For now, allow trading 24/5 (weekdays only)
        current_time = datetime.now()
        weekday = current_time.weekday()
        
        # Monday = 0, Sunday = 6
        if weekday >= 5:  # Saturday or Sunday
            return False
        
        return True
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get a summary of current risk metrics"""
        return {
            'daily_pnl': self.risk_metrics.daily_pnl,
            'daily_loss': self.risk_metrics.daily_loss,
            'daily_profit': self.risk_metrics.daily_profit,
            'concurrent_trades': self.risk_metrics.concurrent_trades,
            'consecutive_losses': self.risk_metrics.consecutive_losses,
            'max_consecutive_losses': self.risk_metrics.max_consecutive_losses,
            'total_trades_today': self.risk_metrics.total_trades_today,
            'active_martingale_sequences': len([s for s in self.martingale_sequences.values() if not s.is_complete]),
            'session_active': self.current_session.is_active if self.current_session else False,
            'session_win_rate': self.current_session.win_rate if self.current_session else 0.0
        }
    
    def get_trading_recommendations(self) -> List[str]:
        """Get trading recommendations based on current risk state"""
        recommendations = []
        
        if self.risk_metrics.consecutive_losses >= 3:
            recommendations.append("Consider reducing position sizes due to consecutive losses")
        
        if self.risk_metrics.daily_loss > settings.max_daily_loss * 0.8:
            recommendations.append("Approaching daily loss limit - trade with caution")
        
        if self.risk_metrics.concurrent_trades >= settings.max_concurrent_trades * 0.8:
            recommendations.append("Approaching maximum concurrent trades limit")
        
        win_rate = self.current_session.win_rate if self.current_session else 0
        if win_rate < 40 and self.current_session and self.current_session.total_trades >= 10:
            recommendations.append("Low win rate detected - consider reviewing strategy")
        
        if not recommendations:
            recommendations.append("Risk levels are within acceptable limits")
        
        return recommendations
    
    def force_stop_trading(self, reason: str):
        """Force stop all trading activities"""
        logger.critical(f"FORCE STOP TRADING: {reason}")
        
        # Mark all martingale sequences as complete
        for sequence in self.martingale_sequences.values():
            if not sequence.is_complete:
                sequence.complete_sequence(TradeStatus.CANCELLED)
        
        # End current session
        if self.current_session and self.current_session.is_active:
            self.end_session()
        
        # Reset metrics to prevent further trading
        self.risk_metrics.consecutive_losses = 999  # High number to block trading