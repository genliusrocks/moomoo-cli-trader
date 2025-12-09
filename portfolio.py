import click
from rich.console import Console
from rich.table import Table
from moomoo import RET_OK, TrdEnv
from connection import ConnectionManager, TRADING_ENV

console = Console()

def get_account_summary():
    """
    Fetches and displays the account assets, cash, and market value.
    """
    ctx = ConnectionManager.get_trade_context()
    
    # 1. Get Funds (Assets, Cash, Market Value)
    # trd_env determines if we are looking at Paper (SIMULATE) or Real (REAL) account
    ret, data = ctx.get_funds(trd_env=TRADING_ENV, currency='USD')

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching funds:[/bold red] {data}")
        return

    # 2. Display using Rich Table
    # The 'data' returned is a pandas DataFrame. We take the first row.
    if not data.empty:
        row = data.iloc[0]
        
        table = Table(title=f"Account Summary ({TRADING_ENV})")

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value (USD)", style="green")

        # Extracting common fields (Field names may vary slightly by API version, standardizing here)
        total_assets = row.get('total_assets', 0.0)
        cash = row.get('cash', 0.0)
        market_val = row.get('market_val', 0.0)
        realized_pl = row.get('realized_pl', 0.0)
        unrealized_pl = row.get('unrealized_pl', 0.0)

        table.add_row("Total Assets", f"${total_assets:,.2f}")
        table.add_row("Cash", f"${cash:,.2f}")
        table.add_row("Market Value", f"${market_val:,.2f}")
        table.add_row("Realized P&L", f"${realized_pl:,.2f}")
        table.add_row("Unrealized P&L", f"${unrealized_pl:,.2f}")

        console.print(table)
    else:
        console.print("[yellow]No account data found.[/yellow]")

    # Close connection after single command use (optional, depending on architecture)
    ConnectionManager.close()