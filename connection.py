import os
from moomoo import OpenSecTradeContext, TrdEnv, SecurityFirm, TrdMarket

# Default Configuration
HOST = os.getenv("MOOMOO_HOST", "127.0.0.1")
PORT = int(os.getenv("MOOMOO_PORT", 11111))
TRADING_ENV = TrdEnv.SIMULATE if os.getenv("MOOMOO_ENV", "SIMULATE") == "SIMULATE" else TrdEnv.REAL

# FIX: Change this to match your account region!
# SecurityFirm.FUTUSECURITIES # <--- Futu HK (Hong Kong)
# SecurityFirm.FUTUINC        # <--- Moomoo US (United States)
# SecurityFirm.FUTUSG         # <--- Moomoo SG (Singapore)
# SecurityFirm.FUTUAU         # <--- Moomoo AU (Australia)

# Since you are a Moomoo US user:
SECURITY_FIRM = SecurityFirm.FUTUINC 

class ConnectionManager:
    _trade_context = None

    @classmethod
    def get_trade_context(cls):
        if cls._trade_context is None:
            try:
                cls._trade_context = OpenSecTradeContext(
                    host=HOST, 
                    port=PORT, 
                    security_firm=SECURITY_FIRM,
                    filter_trdmarket=TrdMarket.US  # Ensure we look for US market permissions
                )
            except Exception as e:
                print(f"[bold red]Error connecting to OpenD:[/bold red] {e}")
                exit(1)
        return cls._trade_context

    @classmethod
    def close(cls):
        if cls._trade_context:
            cls._trade_context.close()
            cls._trade_context = None