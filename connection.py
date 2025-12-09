import os
from moomoo import OpenSecTradeContext, TrdEnv, SecurityFirm

# Default Configuration (can be overridden by environment variables)
HOST = os.getenv("MOOMOO_HOST", "127.0.0.1")
PORT = int(os.getenv("MOOMOO_PORT", 11111))
# Default to SIMULATE for safety, change to REAL for actual trading
TRADING_ENV = TrdEnv.SIMULATE if os.getenv("MOOMOO_ENV", "SIMULATE") == "SIMULATE" else TrdEnv.REAL
# Security Firm: Moomoo defaults to FUTUSECURITIES for most users, change if needed
SECURITY_FIRM = SecurityFirm.FUTUSECURITIES 

class ConnectionManager:
    _trade_context = None

    @classmethod
    def get_trade_context(cls):
        """
        Returns a singleton OpenSecTradeContext instance.
        """
        if cls._trade_context is None:
            try:
                # Initialize the trade context
                cls._trade_context = OpenSecTradeContext(
                    host=HOST, 
                    port=PORT, 
                    security_firm=SECURITY_FIRM
                )
                print(f"Connected to Moomoo OpenD at {HOST}:{PORT} ({TRADING_ENV})")
            except Exception as e:
                print(f"Error connecting to OpenD: {e}")
                exit(1)
        return cls._trade_context

    @classmethod
    def close(cls):
        if cls._trade_context:
            cls._trade_context.close()
            cls._trade_context = None