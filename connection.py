import os
from moomoo import OpenSecTradeContext, OpenQuoteContext, TrdEnv, SecurityFirm, TrdMarket, RET_OK

# Default Configuration
HOST = os.getenv("MOOMOO_HOST", "127.0.0.1")
PORT = int(os.getenv("MOOMOO_PORT", 11111))
TRADING_ENV = TrdEnv.SIMULATE if os.getenv("MOOMOO_ENV", "SIMULATE") == "SIMULATE" else TrdEnv.REAL

# Security Firm
SECURITY_FIRM = SecurityFirm.FUTUINC 

# --- Helper Functions (DRY & Robustness) ---
def safe_float(value):
    """
    Safely converts a value to float. Returns 0.0 if conversion fails.
    Prevents crashes when API returns None or empty strings.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def normalize_ticker(ticker):
    """
    Ensures ticker has a market prefix. Defaults to 'US.' if missing.
    Example: 'AAPL' -> 'US.AAPL'
    """
    ticker = str(ticker).upper().strip()
    if "." not in ticker:
        return f"US.{ticker}"
    return ticker

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
        if cls._quote_context is None:
            try:
                cls._quote_context = OpenQuoteContext(host=HOST, port=PORT)
            except Exception as e:
                print(f"[bold red]Error connecting to Quote Context:[/bold red] {e}")
                exit(1)
        return cls._quote_context

    @classmethod
    def unlock(cls, password):
        """
        Unlocks trading with the given password.
        """
        ctx = cls.get_trade_context()
        ret, data = ctx.unlock_trade(password=password)
        
        if ret == RET_OK:
            print("[bold green]Trading successfully unlocked![/bold green]")
        else:
            print(f"[bold red]Unlock failed:[/bold red] {data}")

    @classmethod
    def close(cls):
        if cls._trade_context:
            cls._trade_context.close()
            cls._trade_context = None
        if cls._quote_context:
            cls._quote_context.close()
            cls._quote_context = None