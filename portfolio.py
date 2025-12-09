import click
from rich.console import Console
from rich.table import Table
from moomoo import RET_OK, TrdEnv
from connection import ConnectionManager, TRADING_ENV
from datetime import datetime, timedelta
import pytz

console = Console()

def safe_float(value):
    """Safely converts a value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def get_account_summary():
    """Fetches and displays account assets."""
    ctx = ConnectionManager.get_trade_context()
    ret, data = ctx.accinfo_query(trd_env=TRADING_ENV, currency='USD')

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching funds:[/bold red] {data}")
        return

    if not data.empty:
        row = data.iloc[0]
        table = Table(title=f"Account Summary ({TRADING_ENV})")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value (USD)", style="green")

        table.add_row("Total Assets", f"${safe_float(row.get('total_assets')):,.2f}")
        table.add_row("Cash", f"${safe_float(row.get('cash')):,.2f}")
        table.add_row("Market Value", f"${safe_float(row.get('market_val')):,.2f}")
        table.add_row("Realized P&L", f"${safe_float(row.get('realized_pl')):,.2f}")
        table.add_row("Unrealized P&L", f"${safe_float(row.get('unrealized_pl')):,.2f}")
        console.print(table)
    else:
        console.print("[yellow]No account data found.[/yellow]")
    
    ConnectionManager.close()

def get_positions():
    """
    Fetches and displays the current stock positions.
    """
    ctx = ConnectionManager.get_trade_context()
    console.print(f"[dim]Fetching positions for {TRADING_ENV}...[/dim]")

    # Fetch positions
    ret, data = ctx.position_list_query(trd_env=TRADING_ENV)

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching positions:[/bold red] {data}")
        ConnectionManager.close()
        return

    if data.empty:
        console.print("[yellow]No positions found. Portfolio is empty.[/yellow]")
        ConnectionManager.close()
        return

    # Create Table
    table = Table(title=f"Current Positions ({TRADING_ENV})")
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Name")
    table.add_column("Qty", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Mkt Val", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("P&L %", justify="right")

    for _, row in data.iterrows():
        qty = safe_float(row.get('qty'))
        # Skip empty positions (sometimes returned with qty=0)
        if qty == 0:
            continue

        cost = safe_float(row.get('cost_price'))
        price = safe_float(row.get('nominal_price'))
        mkt_val = safe_float(row.get('market_val'))
        pl_val = safe_float(row.get('pl_val'))
        pl_ratio = safe_float(row.get('pl_ratio'))

        # Color coding for P&L
        pl_style = "green" if pl_val >= 0 else "red"
        
        table.add_row(
            str(row.get('code')),
            str(row.get('stock_name')),
            f"{qty:,.0f}",
            f"{cost:,.2f}",
            f"{price:,.2f}",
            f"{mkt_val:,.2f}",
            f"[{pl_style}]{pl_val:,.2f}[/{pl_style}]",
            f"[{pl_style}]{pl_ratio:,.2f}%[/{pl_style}]"
        )

    console.print(table)
    ConnectionManager.close()

def get_market_timezone():
    return pytz.timezone('US/Eastern')

def get_deals(days=0, start_date=None, end_date=None):
    ctx = ConnectionManager.get_trade_context()
    market_tz = get_market_timezone()
    now_in_market = datetime.now(market_tz)
    
    is_history = False
    if start_date or (days and days > 0):
        is_history = True

    if is_history:
        if start_date:
            start = start_date
            end = end_date if end_date else now_in_market.strftime("%Y-%m-%d")
        else:
            end = now_in_market.strftime("%Y-%m-%d")
            start = (now_in_market - timedelta(days=days)).strftime("%Y-%m-%d")
            
        console.print(f"[dim]Querying history from {start} to {end}...[/dim]")
        ret, data = ctx.history_deal_list_query(start=start, end=end, trd_env=TRADING_ENV)
    else:
        console.print(f"[dim]Querying today's deals...[/dim]")
        ret, data = ctx.deal_list_query(trd_env=TRADING_ENV)

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching deals:[/bold red] {data}")
        return

    if not data.empty:
        if 'create_time' in data.columns:
            data = data.sort_values(by='create_time', ascending=False)
            
        title = f"Trade History ({TRADING_ENV}) - {'History' if is_history else 'Today'}"
        table = Table(title=title)
        table.add_column("Time", style="cyan")
        table.add_column("Side", style="bold")
        table.add_column("Symbol", style="yellow")
        table.add_column("Price", justify="right")
        table.add_column("Qty", justify="right")
        table.add_column("Amount", justify="right", style="green")

        for _, row in data.iterrows():
            side = row.get('trd_side', 'UNKNOWN')
            side_style = "bold red" if side == "BUY" else "bold green"
            table.add_row(
                str(row.get('create_time', 'N/A')),
                f"[{side_style}]{side}[/{side_style}]",
                str(row.get('code')),
                f"{safe_float(row.get('price')):,.2f}",
                f"{safe_float(row.get('qty')):,.0f}",
                f"{safe_float(row.get('dealt_amount')):,.2f}"
            )
        console.print(table)
    else:
        console.print(f"[yellow]No deals found.[/yellow]")

    ConnectionManager.close()