"""
Compatibility wrapper for quotexpy with Python 3.13+
"""
import sys
import warnings

# Suppress version warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from quotexpy import Quotex
    QUOTEXPY_AVAILABLE = True
    print("✅ quotexpy imported successfully")
except ImportError as e:
    print(f"⚠️ quotexpy import failed: {e}")
    try:
        # Try alternative import
        from quotex_api.stable_api import Quotex
        QUOTEXPY_AVAILABLE = True
        print("✅ quotex_api imported as fallback")
    except ImportError:
        print("❌ No quotex library available - using mock mode")
        
        # Create a mock Quotex class for testing
        class MockQuotex:
            def __init__(self, *args, **kwargs):
                self.connected = False
                self.balance = 1000.0
                
            def connect(self):
                print("🔄 Mock connection (quotexpy not available)")
                self.connected = True
                return True, "Mock connection successful"
                
            def disconnect(self):
                self.connected = False
                
            def get_balance(self):
                return self.balance
                
            def buy(self, asset, amount, direction, duration):
                print(f"🔄 Mock trade: {asset} {direction} ${amount} for {duration}s")
                return f"mock_trade_{hash(f'{asset}{amount}{direction}')}"
                
            def check_win(self, trade_id):
                # Simulate 60% win rate
                import random
                return amount * 0.8 if random.random() < 0.6 else 0
                
            def check_asset_open(self, asset):
                return True
                
            def get_payment(self):
                return {"EURUSD_otc": {"payment": 0.8}}
        
        Quotex = MockQuotex
        QUOTEXPY_AVAILABLE = False

__all__ = ['Quotex', 'QUOTEXPY_AVAILABLE']
