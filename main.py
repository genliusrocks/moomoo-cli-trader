import click
from portfolio import get_account_summary, get_deals, get_positions
from market_data import get_stock_quote
# Import get_orders
from trading import place_trade, get_orders
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
def summary_cmd():
    """Display current assets, cash, and market value."""
    get_account_summary()

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

# --- New Orders Command ---
@cli.command("orders")
def orders_cmd():
    """List all open and recent orders."""
    get_orders()

@cli.command("buy")
@click.argument("ticker")
@click.argument("order_type", type=click.Choice(['limit', 'market'], case_sensitive=False))
@click.argument("qty", type=int)
@click.argument("price", type=float, required=False, default=0.0)
def buy_cmd(ticker, order_type, qty, price):
    """
    Place a BUY order.
    Syntax: python main.py buy <TICKER> <TYPE> <QTY> [PRICE]
    """
    if order_type == 'limit' and price == 0.0:
        click.echo("Error: Limit orders require a price.\nUsage: python main.py buy <TICKER> limit <QTY> <PRICE>")
        return
    place_trade(ticker, 'buy', order_type, price, qty)

@cli.command("sell")
@click.argument("ticker")
@click.argument("order_type", type=click.Choice(['limit', 'market'], case_sensitive=False))
@click.argument("qty", type=int)
@click.argument("price", type=float, required=False, default=0.0)
def sell_cmd(ticker, order_type, qty, price):
    """
    Place a SELL order.
    Syntax: python main.py sell <TICKER> <TYPE> <QTY> [PRICE]
    """
    if order_type == 'limit' and price == 0.0:
        click.echo("Error: Limit orders require a price.\nUsage: python main.py sell <TICKER> limit <QTY> <PRICE>")
        return
    place_trade(ticker, 'sell', order_type, price, qty)

if __name__ == '__main__':
    cli()