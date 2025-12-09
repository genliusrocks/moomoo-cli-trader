import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from moomoo import RET_OK
from connection import ConnectionManager, TRADING_ENV
from datetime import datetime
import pytz

console = Console()

def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def get_account_summary():
    """Fetches and displays the account assets, cash, and market value."""
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

def get_market_timezone():
    return pytz.timezone('US/Eastern')

def get_deals(days=0, start_date=None, end_date=None):
    # This logic matches your previous implementation for fetching deals
    from datetime import timedelta
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
            start_dt = now_in_market - timedelta(days=days)
            start = start_dt.strftime("%Y-%m-%d")
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
        table = Table(title=f"Trade History ({TRADING_ENV})")
        table.add_column("Time", style="dim")
        table.add_column("Side", style="bold")
        table.add_column("Symbol", style="yellow")
        table.add_column("Price", justify="right")
        table.add_column("Qty", justify="right")
        for _, row in data.iterrows():
            side = row.get('trd_side', 'UNKNOWN')
            color = "red" if side == "BUY" else "green"
            table.add_row(
                str(row.get('create_time', 'N/A')),
                f"[{color}]{side}[/{color}]",
                str(row.get('code', 'N/A')),
                f"{safe_float(row.get('price')):,.2f}",
                f"{safe_float(row.get('qty')):,.0f}"
            )
        console.print(table)
    else:
        console.print("[yellow]No deals found.[/yellow]")
    ConnectionManager.close()

def get_statement(date_str=None):
    """
    Fetches a daily statement (Deals + Cash Flow) for a specific date.
    """
    ctx = ConnectionManager.get_trade_context()
    market_tz = get_market_timezone()
    
    # 1. Parse Date
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%y%m%d")
            query_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            console.print(f"[bold red]Invalid date format:[/bold red] {date_str}. Use YYMMDD.")
            return
    else:
        query_date = datetime.now(market_tz).strftime("%Y-%m-%d")

    console.print(f"[dim]Generating statement for [bold white]{query_date}[/bold white]...[/dim]")

    # 2. Fetch Trades (Uses start/end)
    ret_deals, data_deals = ctx.history_deal_list_query(
        start=query_date, end=query_date, trd_env=TRADING_ENV
    )

    # 3. Fetch Cash Flow (FIX: Uses clearing_date)
    # The API requires querying one day at a time for this specific endpoint
    ret_flow, data_flow = ctx.get_acc_cash_flow(
        clearing_date=query_date, trd_env=TRADING_ENV
    )

    # --- Display Trades ---
    if ret_deals == RET_OK and not data_deals.empty:
        deal_table = Table(title="Executed Trades", style="blue")
        deal_table.add_column("Time", style="dim")
        deal_table.add_column("Side")
        deal_table.add_column("Symbol", style="yellow")
        deal_table.add_column("Price", justify="right")
        deal_table.add_column("Qty", justify="right")
        deal_table.add_column("Amount", justify="right")

        for _, row in data_deals.iterrows():
            side = row.get('trd_side', 'UNKNOWN')
            color = "red" if side == "BUY" else "green"
            deal_table.add_row(
                str(row.get('create_time', 'N/A'))[11:], 
                f"[{color}]{side}[/{color}]",
                str(row.get('code', 'N/A')),
                f"{safe_float(row.get('price')):,.2f}",
                f"{safe_float(row.get('qty')):,.0f}",
                f"{safe_float(row.get('dealt_amount')):,.2f}"
            )
        console.print(deal_table)
    else:
        console.print(Panel("No trades executed on this day.", title="Trades", style="dim"))

    # --- Display Cash Flow ---
    if ret_flow == RET_OK and not data_flow.empty:
        flow_table = Table(title="Cash Flow / Settlements", style="magenta")
        flow_table.add_column("Time", style="dim")
        flow_table.add_column("Type")
        flow_table.add_column("Amount", justify="right")
        flow_table.add_column("Description", style="dim")

        for _, row in data_flow.iterrows():
            amt = safe_float(row.get('cash_flow_amount', 0))
            color = "green" if amt >= 0 else "red"
            time_val = str(row.get('create_time', row.get('pay_time', 'N/A')))
            if len(time_val) > 10: time_val = time_val[11:]

            flow_table.add_row(
                time_val,
                str(row.get('cash_flow_name', 'Unknown')),
                f"[{color}]{amt:,.2f}[/{color}]",
                str(row.get('cash_flow_remark', '')) # 'cashflow_remark' or 'description'
            )
        console.print(flow_table)
    else:
        console.print(Panel("No cash flow events.", title="Cash Flow", style="dim"))

    ConnectionManager.close()