import click
from rich.console import Console
from rich.table import Table
from moomoo import RET_OK, TrdEnv
from connection import ConnectionManager, TRADING_ENV

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
    
    # 1. Get Funds (Assets, Cash, Market Value)
    # Using accinfo_query (correct method name)
    ret, data = ctx.accinfo_query(trd_env=TRADING_ENV, currency='USD')

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching funds:[/bold red] {data}")
        return

    # 2. Display using Rich Table
    if not data.empty:
        row = data.iloc[0]
        
        table = Table(title=f"Account Summary ({TRADING_ENV})")

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value (USD)", style="green")

        # Extracting and sanitizing fields
        # We use safe_float to ensure we can format them as numbers
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

    # Close connection
    ConnectionManager.close()