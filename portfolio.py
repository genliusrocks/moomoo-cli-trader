import click
from rich.console import Console
from rich.table import Table
from moomoo import RET_OK, TrdEnv
from connection import ConnectionManager, TRADING_ENV
from datetime import datetime, timedelta
import pytz  # 确保你已经安装了 pytz: pip install pytz

console = Console()

def safe_float(value):
    """
    Safely converts a value to float. Returns 0.0 if conversion fails.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def get_account_summary():
    """
    Fetches and displays the account assets, cash, and market value.
    """
    ctx = ConnectionManager.get_trade_context()
    
    # 1. Get Funds
    ret, data = ctx.accinfo_query(trd_env=TRADING_ENV, currency='USD')

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching funds:[/bold red] {data}")
        # ConnectionManager.close() # Optional: keep open if reused
        return

    # 2. Display using Rich Table
    if not data.empty:
        row = data.iloc[0]
        
        table = Table(title=f"Account Summary ({TRADING_ENV})")

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value (USD)", style="green")

        total_assets = safe_float(row.get('total_assets'))
        cash = safe_float(row.get('cash'))
        market_val = safe_float(row.get('market_val'))
        realized_pl = safe_float(row.get('realized_pl'))
        unrealized_pl = safe_float(row.get('unrealized_pl'))

        table.add_row("Total Assets", f"${total_assets:,.2f}")
        table.add_row("Cash", f"${cash:,.2f}")
        table.add_row("Market Value", f"${market_val:,.2f}")
        table.add_row("Realized P&L", f"${realized_pl:,.2f}")
        table.add_row("Unrealized P&L", f"${unrealized_pl:,.2f}")

        console.print(table)
    else:
        console.print("[yellow]No account data found.[/yellow]")

    ConnectionManager.close()

def get_market_timezone():
    """
    Returns the market timezone. Defaults to US/Eastern for Moomoo US.
    """
    return pytz.timezone('US/Eastern')

def get_deals(days=0, start_date=None, end_date=None):
    """
    Fetches executed trades. 
    Auto-handles timezone to ensure 'Today' matches the market's today.
    """
    ctx = ConnectionManager.get_trade_context()
    
    # Get Market Time
    market_tz = get_market_timezone()
    now_in_market = datetime.now(market_tz)
    
    is_history = False
    
    # Check if we need history interface
    if start_date or (days and days > 0):
        is_history = True

    if is_history:
        if start_date:
            start = start_date
            end = end_date if end_date else now_in_market.strftime("%Y-%m-%d")
        else:
            end = now_in_market.strftime("%Y-%m-%d")
            start_dt = now_in_market - timedelta(days=days)
            start = start_dt.strftime("%Y-%m-%d")
            
        console.print(f"[dim]Querying history from {start} to {end} (Market Time: {market_tz.zone})...[/dim]")
        
        ret, data = ctx.history_deal_list_query(
            start=start, 
            end=end, 
            trd_env=TRADING_ENV
        )
    else:
        # Query Today
        console.print(f"[dim]Querying today's deals (Market Date: {now_in_market.strftime('%Y-%m-%d')})...[/dim]")
        ret, data = ctx.deal_list_query(trd_env=TRADING_ENV)

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching deals:[/bold red] {data}")
        return

    if not data.empty:
        if 'create_time' in data.columns:
            data = data.sort_values(by='create_time', ascending=False)
            
        title = f"Trade History ({TRADING_ENV}) - {'History' if is_history else 'Today'}"
        table = Table(title=title)

        table.add_column("Time (Market)", style="cyan", no_wrap=True)
        table.add_column("Side", style="bold")
        table.add_column("Symbol", style="yellow")
        table.add_column("Price", justify="right")
        table.add_column("Qty", justify="right")
        table.add_column("Amount", justify="right", style="green")

        for _, row in data.iterrows():
            side = row.get('trd_side', 'UNKNOWN')
            side_style = "bold red" if side == "BUY" else "bold green"

            time_str = str(row.get('create_time', 'N/A'))
            code = str(row.get('code', 'N/A'))
            price = safe_float(row.get('price'))
            qty = safe_float(row.get('qty'))
            amount = safe_float(row.get('dealt_amount'))

            table.add_row(
                time_str,
                f"[{side_style}]{side}[/{side_style}]",
                code,
                f"{price:,.2f}",
                f"{qty:,.0f}",
                f"{amount:,.2f}"
            )

        console.print(table)
    else:
        console.print(f"[yellow]No deals found for this period ({'History' if is_history else 'Today'}).[/yellow]")

    ConnectionManager.close()