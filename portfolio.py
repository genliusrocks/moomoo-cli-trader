import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from moomoo import RET_OK, TrdEnv
# Modified: Import safe_float from connection
from connection import ConnectionManager, TRADING_ENV, safe_float
from datetime import datetime
import pytz

console = Console()

def get_account_summary(currency='USD'):  # <--- 新增参数
    """Fetches and displays the account assets, cash, and market value."""
    ctx = ConnectionManager.get_trade_context()
    
    # 使用传入的 currency 参数
    ret, data = ctx.accinfo_query(trd_env=TRADING_ENV, currency=currency)
    
    if ret != RET_OK:
        console.print(f"[bold red]Error fetching funds ({currency}):[/bold red] {data}")
        return
    if not data.empty:
        row = data.iloc[0]
        # 标题增加币种显示
        table = Table(title=f"Account Summary ({TRADING_ENV}) - {currency}")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column(f"Value ({currency})", style="green") # 列名增加币种
        
        table.add_row("Total Assets", f"{safe_float(row.get('total_assets')):,.2f}")
        table.add_row("Cash", f"{safe_float(row.get('cash')):,.2f}")
        table.add_row("Market Value", f"{safe_float(row.get('market_val')):,.2f}")
        table.add_row("Realized P&L", f"{safe_float(row.get('realized_pl')):,.2f}")
        table.add_row("Unrealized P&L", f"{safe_float(row.get('unrealized_pl')):,.2f}")
        console.print(table)
    else:
        console.print(f"[yellow]No account data found for {currency}.[/yellow]")
    ConnectionManager.close()

def get_market_timezone():
    return pytz.timezone('US/Eastern')

def get_deals(days=0, start_date=None, end_date=None):
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

def get_positions():
    """
    Fetches and displays the current stock positions.
    """
    ctx = ConnectionManager.get_trade_context()
    console.print(f"[dim]Fetching positions for {TRADING_ENV}...[/dim]")

    ret, data = ctx.position_list_query(trd_env=TRADING_ENV)

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching positions:[/bold red] {data}")
        ConnectionManager.close()
        return

    if not data.empty:
        table = Table(title=f"Current Positions ({TRADING_ENV})")
        
        table.add_column("Symbol", style="yellow")
        table.add_column("Name")
        table.add_column("Qty", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Market Val", justify="right")
        table.add_column("P&L", justify="right")
        table.add_column("P&L %", justify="right")

        for _, row in data.iterrows():
            code = str(row.get('code', 'N/A'))
            name = str(row.get('stock_name', 'N/A'))
            qty = safe_float(row.get('qty'))
            cost = safe_float(row.get('cost_price'))
            price = safe_float(row.get('nominal_price'))
            mkt_val = safe_float(row.get('market_val'))
            pl_val = safe_float(row.get('pl_val'))
            pl_ratio = safe_float(row.get('pl_ratio'))

            # P&L Color: Green for profit, Red for loss (US Standard)
            pl_style = "green" if pl_val >= 0 else "red"
            
            table.add_row(
                code,
                name,
                f"{qty:,.0f}",
                f"{cost:,.2f}",
                f"{price:,.2f}",
                f"{mkt_val:,.2f}",
                f"[{pl_style}]{pl_val:+,.2f}[/{pl_style}]",
                f"[{pl_style}]{pl_ratio:+.2f}%[/{pl_style}]"
            )
        
        console.print(table)
    else:
        console.print("[yellow]No positions found (Empty portfolio).[/yellow]")

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

    # 2. Fetch Trades
    ret_deals, data_deals = ctx.history_deal_list_query(
        start=query_date, end=query_date, trd_env=TRADING_ENV
    )

    # 3. Fetch Fees
    fees_map = {} 
    if ret_deals == RET_OK and not data_deals.empty:
        order_ids = list(set(data_deals['order_id'].tolist()))
        ret_fee, data_fee = ctx.order_fee_query(order_id_list=order_ids, trd_env=TRADING_ENV)
        
        if ret_fee == RET_OK and not data_fee.empty:
            for _, row in data_fee.iterrows():
                oid = row.get('order_id')
                amt = safe_float(row.get('fee_amount'))
                if oid in fees_map:
                    fees_map[oid] += amt
                else:
                    fees_map[oid] = amt

    # 4. Fetch Cash Flow
    ret_flow, data_flow = ctx.get_acc_cash_flow(
        clearing_date=query_date, trd_env=TRADING_ENV
    )

    # --- Display Trades ---
    total_fees_day = 0.0
    if ret_deals == RET_OK and not data_deals.empty:
        deal_table = Table(title=f"Executed Trades ({query_date})", style="blue")
        deal_table.add_column("Time", style="dim")
        deal_table.add_column("Side")
        deal_table.add_column("Symbol", style="yellow")
        deal_table.add_column("Price", justify="right")
        deal_table.add_column("Qty", justify="right")
        deal_table.add_column("Amount", justify="right")
        deal_table.add_column("Order Fee", justify="right", style="red")

        processed_orders = set()

        for _, row in data_deals.iterrows():
            side = row.get('trd_side', 'UNKNOWN')
            color = "red" if side == "BUY" else "green"
            
            price = safe_float(row.get('price'))
            qty = safe_float(row.get('qty'))
            # Manually calc amount
            amount = price * qty
            
            order_id = row.get('order_id')
            fee_display = "-"
            
            if order_id in fees_map:
                fee_val = fees_map[order_id]
                if order_id not in processed_orders:
                    fee_display = f"{fee_val:.2f}"
                    total_fees_day += fee_val
                    processed_orders.add(order_id)
                else:
                    fee_display = "(see above)"

            deal_table.add_row(
                str(row.get('create_time', 'N/A'))[11:], 
                f"[{color}]{side}[/{color}]",
                str(row.get('code', 'N/A')),
                f"{price:,.2f}",
                f"{qty:,.0f}",
                f"{amount:,.2f}",
                fee_display
            )
        console.print(deal_table)
        console.print(f"[dim right]Total Fees for displayed orders: ${total_fees_day:.2f}[/dim right]")
    else:
        console.print(Panel("No trades executed on this day.", title="Trades", style="dim"))

    # --- Display Cash Flow ---
    if ret_flow == RET_OK and not data_flow.empty:
        flow_table = Table(title=f"Cash Flow / Settlements ({query_date})", style="magenta")
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
                str(row.get('cash_flow_remark', '')) 
            )
        console.print(flow_table)
    else:
        console.print(Panel(f"No cash flow settled on {query_date}.", title="Cash Flow", style="dim"))

    ConnectionManager.close()
