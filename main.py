import click
from portfolio import get_account_summary, get_deals, get_positions
from market_data import get_stock_quote
from trading import place_trade
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

# --- Buy Command (Updated) ---
@cli.command("buy")
@click.argument("ticker")
@click.argument("order_type", type=click.Choice(['limit', 'market'], case_sensitive=False))
@click.argument("qty", type=int)
@click.argument("price", type=float, required=False, default=0.0)
def buy_cmd(ticker, order_type, qty, price):
    """
    Place a BUY order.
    
    Syntax:
    Market: python main.py buy AAPL market 100
    Limit:  python main.py buy AAPL limit 100 273.5
    """
    # Validation: Limit orders must have a price
    if order_type == 'limit' and price == 0.0:
        click.echo("Error: Limit orders require a price.\nUsage: python main.py buy <TICKER> limit <QTY> <PRICE>")
        return

    place_trade(ticker, 'buy', order_type, price, qty)

# --- Sell Command (Updated) ---
@cli.command("sell")
@click.argument("ticker")
@click.argument("order_type", type=click.Choice(['limit', 'market'], case_sensitive=False))
@click.argument("qty", type=int)
@click.argument("price", type=float, required=False, default=0.0)
def sell_cmd(ticker, order_type, qty, price):
    """
    Place a SELL order.
    
    Syntax:
    Market: python main.py sell SPY market 10
    Limit:  python main.py sell SPY limit 10 685.5
    """
    if order_type == 'limit' and price == 0.0:
        click.echo("Error: Limit orders require a price.\nUsage: python main.py sell <TICKER> limit <QTY> <PRICE>")
        return

    place_trade(ticker, 'sell', order_type, price, qty)

if __name__ == '__main__':
    cli()