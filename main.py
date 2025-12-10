import click
from portfolio import get_account_summary, get_deals, get_statement, get_positions
from market_data import get_stock_quote
from trading import place_trade, get_orders, cancel_order 
from connection import ConnectionManager

@click.group()
def cli():
    """Moomoo CLI Trader - A terminal-based trading tool."""
    pass

@cli.group()
def portfolio():
    """Manage portfolio and view account details."""
    pass

@portfolio.command("summary")
@click.option("--currency", default="USD", type=click.Choice(["USD", "HKD", "CNH"]), help="Currency to display (USD, HKD, CNH).")
def summary_cmd(currency):
    """
    Display current assets, cash, and market value.
    Example: python main.py portfolio summary --currency HKD
    """
    get_account_summary(currency)

@portfolio.command("positions")
def positions_cmd():
    """List current stock holdings."""
    get_positions()

@portfolio.command("deals")
@click.option("--days", default=0, help="Number of past days to fetch.")
@click.option("--start", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--end", default=None, help="End date (YYYY-MM-DD)")
def deals_cmd(days, start, end):
    """List executed trades (Deals). Defaults to Today."""
    get_deals(days=days, start_date=start, end_date=end)

# --- STATEMENT COMMAND ---
@cli.command("statement")
@click.argument("date_str", required=False)
def statement_cmd(date_str):
    """
    Get daily statement (Trades & Cash Flow).
    DATE_STR: Optional 'YYMMDD' (e.g. 241209). Defaults to Today if omitted.
    """
    get_statement(date_str)

@cli.command("quote")
@click.argument("ticker")
def quote_cmd(ticker):
    """Get real-time quote."""
    get_stock_quote(ticker)

@cli.command("unlock")
@click.argument("password")
def unlock_cmd(password):
    """Unlock trading with 6-digit PIN."""
    ConnectionManager.unlock(password)

@cli.command("orders")
def orders_cmd():
    """List all open and recent orders."""
    get_orders()

@cli.command("cancel")
@click.argument("order_id")
def cancel_cmd(order_id):
    """
    Cancel an open order.
    Example: python main.py cancel 657248
    """
    cancel_order(order_id)

# --- Updated Buy/Sell Commands ---

ORDER_TYPES = ['LIMIT', 'MARKET', 'STOP', 'STOP_LIMIT', 'MIT', 'LIT', 'TR_STOP', 'TR_STOP_LIMIT']

@cli.command("buy")
@click.argument("ticker")
@click.argument("order_type", type=click.Choice(ORDER_TYPES, case_sensitive=False))
@click.argument("qty", type=int)
@click.argument("price", type=float, required=False, default=0.0)
# New Options for Advanced Orders
@click.option("--aux", type=float, default=0.0, help="Trigger Price (for STOP/MIT/LIT).")
@click.option("--trail", type=float, default=0.0, help="Trailing Value (Amount or Ratio).")
@click.option("--trail_type", type=click.Choice(['amount', 'ratio'], case_sensitive=False), default='amount', help="Trailing Type (default: amount).")
@click.option("--spread", type=float, default=0.0, help="Limit Spread (for Trailing Stop Limit).")
def buy_cmd(ticker, order_type, qty, price, aux, trail, trail_type, spread):
    """
    Place a BUY order.
    
    Examples:
    \b
    Market:  buy AAPL market 10
    Limit:   buy AAPL limit 10 150.5
    Stop:    buy AAPL stop 10 0 --aux 155.0
    Trail:   buy AAPL tr_stop 10 0 --trail 2.0 --trail_type amount
    """
    place_trade(ticker, 'buy', order_type, price, qty, 
                aux_price=aux, trail_type=trail_type, trail_value=trail, trail_spread=spread)

@cli.command("sell")
@click.argument("ticker")
@click.argument("order_type", type=click.Choice(ORDER_TYPES, case_sensitive=False))
@click.argument("qty", type=int)
@click.argument("price", type=float, required=False, default=0.0)
@click.option("--aux", type=float, default=0.0, help="Trigger Price (for STOP/MIT/LIT).")
@click.option("--trail", type=float, default=0.0, help="Trailing Value (Amount or Ratio).")
@click.option("--trail_type", type=click.Choice(['amount', 'ratio'], case_sensitive=False), default='amount', help="Trailing Type.")
@click.option("--spread", type=float, default=0.0, help="Limit Spread (for Trailing Stop Limit).")
def sell_cmd(ticker, order_type, qty, price, aux, trail, trail_type, spread):
    """
    Place a SELL order.
    
    Examples:
    \b
    Stop:    sell AAPL stop 10 0 --aux 140.0
    Trail:   sell AAPL tr_stop 10 0 --trail 5.0 --trail_type ratio
    """
    place_trade(ticker, 'sell', order_type, price, qty, 
                aux_price=aux, trail_type=trail_type, trail_value=trail, trail_spread=spread)

if __name__ == '__main__':
    cli()
