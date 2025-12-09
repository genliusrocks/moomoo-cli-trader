import click
from portfolio import get_account_summary, get_deals
from market_data import get_stock_quote

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

# --- New Quote Command ---
@cli.command("quote")
@click.argument("ticker")
def quote_cmd(ticker):
    """Get real-time quote and Level-2 order book for a stock (e.g., AAPL)."""
    get_stock_quote(ticker)

if __name__ == '__main__':
    cli()