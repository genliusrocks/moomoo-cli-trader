import click
from portfolio import get_account_summary, get_deals
from market_data import get_stock_quote
from trading import place_trade
from connection import ConnectionManager # Import ConnectionManager directly

@click.group()
def cli():
    """Moomoo CLI Trader - A terminal-based trading tool."""
    pass

@cli.group()
def portfolio():
    """Manage portfolio and view account details."""
    pass

@portfolio.command("summary")
def summary_cmd():
    """Display current assets, cash, and market value."""
    get_account_summary()

@portfolio.command("deals")
@click.option("--days", default=0, help="Number of past days to fetch (e.g., 7 for past week). Default 0 is Today only.")
@click.option("--start", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--end", default=None, help="End date (YYYY-MM-DD)")
def deals_cmd(days, start, end):
    """List executed trades (Deals). Defaults to Today."""
    get_deals(days=days, start_date=start, end_date=end)

@cli.command("quote")
@click.argument("ticker")
def quote_cmd(ticker):
    """Get real-time quote and Level-2 order book for a stock (e.g., AAPL)."""
    get_stock_quote(ticker)

@cli.command("buy")
@click.argument("ticker")
@click.argument("order_type", type=click.Choice(['limit', 'market'], case_sensitive=False))
@click.argument("price", type=float)
@click.argument("qty", type=int)
def buy_cmd(ticker, order_type, price, qty):
    """
    Place a BUY order.
    Example: python main.py buy AAPL limit 273.1 100
    """
    place_trade(ticker, 'buy', order_type, price, qty)

# --- New Unlock Command ---
@cli.command("unlock")
@click.argument("password")
def unlock_cmd(password):
    """Unlock trading with your 6-digit trading password."""
    ConnectionManager.unlock(password)

if __name__ == '__main__':
    cli()