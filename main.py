#!/usr/bin/env python3
"""
QXBroker Auto Trading Bot with Telegram Signal Integration
Main application entry point
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

from colorama import init, Fore, Style
from termcolor import colored

# Initialize colorama for Windows compatibility
init()

from config import settings
from core.models import TradingSignal, Trade, TradeStatus
from brokers import QXBrokerClient
from telegram_integration import TelegramSignalClient
from trading import RiskManager, TradeExecutor

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('websocket').setLevel(logging.WARNING)

class TradingBot:
    """Main trading bot application"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.broker_client: Optional[QXBrokerClient] = None
        self.telegram_client: Optional[TelegramSignalClient] = None
        self.risk_manager: Optional[RiskManager] = None
        self.trade_executor: Optional[TradeExecutor] = None
        
        # Control flags
        self.is_running = False
        self.shutdown_requested = False
        
        # Statistics
        self.start_time = datetime.now()
        self.total_signals_received = 0
        self.total_trades_executed = 0
        
    async def initialize(self) -> bool:
        """Initialize all bot components"""
        try:
            self.logger.info("Initializing QXBroker Auto Trading Bot...")
            
            # Print welcome message
            self._print_welcome()
            
            # Initialize broker client
            self.logger.info("Initializing broker client...")
            self.broker_client = QXBrokerClient()
            
            # Connect to broker
            if not await self.broker_client.connect():
                self.logger.error("Failed to connect to broker")
                return False
            
            # Get initial balance
            initial_balance = await self.broker_client.get_balance()
            if initial_balance is None:
                self.logger.error("Could not get initial balance")
                return False
            
            self.logger.info(f"Connected to broker. Initial balance: ${initial_balance}")
            
            # Initialize risk manager
            self.logger.info("Initializing risk manager...")
            self.risk_manager = RiskManager()
            self.risk_manager.start_session(initial_balance)
            
            # Initialize trade executor
            self.logger.info("Initializing trade executor...")
            self.trade_executor = TradeExecutor(self.broker_client, self.risk_manager)
            
            # Set up callbacks
            self.trade_executor.set_trade_callback(self._on_trade_update)
            self.trade_executor.set_signal_callback(self._on_signal_processed)
            
            # Initialize Telegram client
            self.logger.info("Initializing Telegram client...")
            self.telegram_client = TelegramSignalClient(self._on_signal_received)
            
            if not await self.telegram_client.connect():
                self.logger.error("Failed to connect to Telegram")
                return False
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {str(e)}")
            return False
    
    async def start(self):
        """Start the trading bot"""
        if self.is_running:
            self.logger.warning("Bot is already running")
            return
        
        self.logger.info("Starting trading bot...")
        self.is_running = True
        
        try:
            # Start all components
            tasks = []
            
            # Start trade executor
            if self.trade_executor:
                tasks.append(asyncio.create_task(self.trade_executor.start()))
            
            # Start broker health check
            if self.broker_client:
                tasks.append(asyncio.create_task(self.broker_client.health_check()))
                tasks.append(asyncio.create_task(self.broker_client.monitor_active_trades()))
            
            # Start Telegram client
            if self.telegram_client:
                tasks.append(asyncio.create_task(self.telegram_client.run_until_disconnected()))
            
            # Start status monitor
            tasks.append(asyncio.create_task(self._status_monitor()))
            
            self.logger.info("🚀 Trading bot started successfully!")
            self._print_status()
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"Error running bot: {str(e)}")
        finally:
            self.is_running = False
    
    async def stop(self):
        """Stop the trading bot"""
        if not self.is_running:
            self.logger.warning("Bot is not running")
            return
        
        self.logger.info("Stopping trading bot...")
        self.shutdown_requested = True
        
        try:
            # Stop trade executor
            if self.trade_executor:
                await self.trade_executor.stop()
            
            # Disconnect from broker
            if self.broker_client:
                await self.broker_client.disconnect()
            
            # Disconnect from Telegram
            if self.telegram_client:
                await self.telegram_client.disconnect()
            
            # End trading session
            if self.risk_manager:
                final_balance = None
                if self.broker_client:
                    final_balance = await self.broker_client.get_balance()
                self.risk_manager.end_session(final_balance)
            
            self.logger.info("Trading bot stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {str(e)}")
    
    async def _on_signal_received(self, signal: TradingSignal):
        """Handle received trading signals"""
        try:
            self.total_signals_received += 1
            self.logger.info(f"📊 Signal received: {signal.asset} {signal.direction.value.upper()} ${signal.amount}")
            
            # Add signal to trade executor
            if self.trade_executor:
                await self.trade_executor.add_signal(signal)
            
            # Send notification to Telegram (optional)
            if self.telegram_client and settings.telegram_chat_id:
                await self.telegram_client.send_trade_notification(
                    settings.telegram_chat_id, 
                    signal
                )
                
        except Exception as e:
            self.logger.error(f"Error handling signal: {str(e)}")
    
    async def _on_trade_update(self, trade: Trade):
        """Handle trade updates"""
        try:
            self.logger.info(f"📈 Trade update: {trade.asset} {trade.direction.value.upper()} - {trade.status.value.upper()}")
            
            # Send notification to Telegram
            if self.telegram_client and settings.telegram_chat_id:
                result_text = f"{trade.status.value.upper()}"
                if trade.profit_loss is not None:
                    if trade.status == TradeStatus.WON:
                        result_text += f" (+${trade.profit_loss:.2f})"
                    else:
                        result_text += f" (-${trade.amount:.2f})"
                
                # Create signal for notification
                signal = TradingSignal(
                    asset=trade.asset,
                    direction=trade.direction,
                    amount=trade.amount,
                    duration=trade.duration
                )
                
                await self.telegram_client.send_trade_notification(
                    settings.telegram_chat_id,
                    signal,
                    result_text
                )
                
        except Exception as e:
            self.logger.error(f"Error handling trade update: {str(e)}")
    
    async def _on_signal_processed(self, signal: TradingSignal, message: str):
        """Handle signal processing results"""
        try:
            self.logger.debug(f"Signal processed: {signal.asset} - {message}")
            
        except Exception as e:
            self.logger.error(f"Error handling signal processing: {str(e)}")
    
    async def _status_monitor(self):
        """Monitor bot status and print periodic updates"""
        while self.is_running and not self.shutdown_requested:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                if not self.shutdown_requested:
                    self._print_status()
                    
            except Exception as e:
                self.logger.error(f"Error in status monitor: {str(e)}")
                await asyncio.sleep(60)
    
    def _print_welcome(self):
        """Print welcome message"""
        print("\n" + "="*60)
        print(colored("🤖 QXBroker Auto Trading Bot", "cyan", attrs=["bold"]))
        print(colored("📈 Telegram Signal Integration", "green"))
        print("="*60)
        print(f"📊 Broker: {settings.qxbroker_host}")
        print(f"💰 Mode: {settings.qxbroker_mode}")
        print(f"📱 Telegram: {'✅ Configured' if settings.telegram_api_id else '❌ Not configured'}")
        print(f"⚡ Martingale: {'✅ Enabled' if settings.martingale_enabled else '❌ Disabled'}")
        print("="*60 + "\n")
    
    def _print_status(self):
        """Print current bot status"""
        try:
            uptime = datetime.now() - self.start_time
            
            # Get statistics
            executor_stats = self.trade_executor.get_statistics() if self.trade_executor else {}
            risk_summary = self.risk_manager.get_risk_summary() if self.risk_manager else {}
            broker_status = self.broker_client.get_connection_status() if self.broker_client else None
            telegram_stats = self.telegram_client.get_statistics() if self.telegram_client else {}
            
            print("\n" + "="*60)
            print(colored(f"📊 Bot Status - {datetime.now().strftime('%H:%M:%S')}", "yellow", attrs=["bold"]))
            print("="*60)
            
            # Connection status
            broker_status_text = "✅ Connected" if broker_status and broker_status.is_connected else "❌ Disconnected"
            telegram_status_text = "✅ Connected" if telegram_stats.get('is_connected') else "❌ Disconnected"
            
            print(f"🔗 Broker: {broker_status_text}")
            print(f"📱 Telegram: {telegram_status_text}")
            print(f"⏱️  Uptime: {str(uptime).split('.')[0]}")
            
            # Balance and P&L
            if broker_status and broker_status.balance is not None:
                print(f"💰 Balance: ${broker_status.balance:.2f}")
            
            if risk_summary:
                daily_pnl = risk_summary.get('daily_pnl', 0)
                pnl_color = "green" if daily_pnl >= 0 else "red"
                pnl_symbol = "+" if daily_pnl >= 0 else ""
                print(colored(f"📈 Daily P&L: {pnl_symbol}${daily_pnl:.2f}", pnl_color))
            
            # Trading statistics
            print(f"📊 Signals: {self.total_signals_received}")
            print(f"🎯 Trades: {executor_stats.get('trades_executed', 0)}")
            print(f"✅ Won: {executor_stats.get('trades_won', 0)}")
            print(f"❌ Lost: {executor_stats.get('trades_lost', 0)}")
            
            win_rate = executor_stats.get('win_rate', 0)
            win_rate_color = "green" if win_rate >= 60 else "yellow" if win_rate >= 40 else "red"
            print(colored(f"📊 Win Rate: {win_rate:.1f}%", win_rate_color))
            
            # Active trades
            active_trades = executor_stats.get('active_trades', 0)
            if active_trades > 0:
                print(f"⚡ Active Trades: {active_trades}")
            
            # Risk metrics
            if risk_summary:
                consecutive_losses = risk_summary.get('consecutive_losses', 0)
                if consecutive_losses > 0:
                    print(colored(f"⚠️  Consecutive Losses: {consecutive_losses}", "yellow"))
            
            print("="*60 + "\n")
            
        except Exception as e:
            self.logger.error(f"Error printing status: {str(e)}")
    
    def get_full_statistics(self) -> dict:
        """Get comprehensive bot statistics"""
        uptime = datetime.now() - self.start_time
        
        stats = {
            'uptime_seconds': uptime.total_seconds(),
            'start_time': self.start_time.isoformat(),
            'is_running': self.is_running,
            'total_signals_received': self.total_signals_received,
            'broker_status': self.broker_client.get_connection_status().dict() if self.broker_client else None,
            'executor_stats': self.trade_executor.get_statistics() if self.trade_executor else {},
            'risk_summary': self.risk_manager.get_risk_summary() if self.risk_manager else {},
            'telegram_stats': self.telegram_client.get_statistics() if self.telegram_client else {}
        }
        
        return stats

# Global bot instance
bot = None

async def main():
    """Main application entry point"""
    global bot
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        if bot:
            asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and initialize bot
        bot = TradingBot()
        
        if not await bot.initialize():
            logger.error("Failed to initialize bot")
            return 1
        
        # Start bot
        await bot.start()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1
    finally:
        if bot:
            await bot.stop()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)