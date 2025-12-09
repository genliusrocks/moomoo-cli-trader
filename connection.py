import os
from moomoo import OpenSecTradeContext, OpenQuoteContext, TrdEnv, SecurityFirm, TrdMarket

# Default Configuration
HOST = os.getenv("MOOMOO_HOST", "127.0.0.1")
PORT = int(os.getenv("MOOMOO_PORT", 11111))
TRADING_ENV = TrdEnv.SIMULATE if os.getenv("MOOMOO_ENV", "SIMULATE") == "SIMULATE" else TrdEnv.REAL

# Security Firm
SECURITY_FIRM = SecurityFirm.FUTUINC 

class ConnectionManager:
    _trade_context = None
    _quote_context = None

    @classmethod
    def get_trade_context(cls):
        if cls._trade_context is None:
            try:
                cls._trade_context = OpenSecTradeContext(
                    host=HOST, 
                    port=PORT, 
                    security_firm=SECURITY_FIRM,
                    filter_trdmarket=TrdMarket.US
                )
            except Exception as e:
                print(f"[bold red]Error connecting to Trade Context:[/bold red] {e}")
                exit(1)
        return cls._trade_context

    @classmethod
    def get_quote_context(cls):
        """
        Returns a singleton OpenQuoteContext instance for Market Data.
        """
        if cls._quote_context is None:
            try:
                # Quote context only needs host and port
                cls._quote_context = OpenQuoteContext(host=HOST, port=PORT)
            except Exception as e:
                print(f"[bold red]Error connecting to Quote Context:[/bold red] {e}")
                exit(1)
        return cls._quote_context

    @classmethod
    def close(cls):
        if cls._trade_context:
            cls._trade_context.close()
            cls._trade_context = None
        if cls._quote_context:
            cls._quote_context.close()
            cls._quote_context = None