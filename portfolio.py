import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from moomoo import RET_OK
from connection import ConnectionManager, TRADING_ENV, safe_float
from datetime import datetime, timedelta
import pytz
import pandas as pd

console = Console()

# ... (保持 get_account_summary, get_market_timezone, get_deals, get_positions 不变) ...
# 为了节省篇幅，这里仅展示你需要修改的 get_statement 部分，
# 请确保保留文件顶部的 imports 和其他函数。
# 如果你需要完整文件，请告诉我。

def get_account_summary(currency='USD'):
    """Fetches and displays the account assets, cash, and market value."""
    ctx = ConnectionManager.get_trade_context()
    ret, data = ctx.accinfo_query(trd_env=TRADING_ENV, currency=currency)
    if ret != RET_OK:
        console.print(f"[bold red]Error fetching funds ({currency}):[/bold red] {data}")
        return
    if not data.empty:
        row = data.iloc[0]
        table = Table(title=f"Account Summary ({TRADING_ENV}) - {currency}")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column(f"Value ({currency})", style="green")
        
        table.add_row("Total Assets", f"${safe_float(row.get('total_assets')):,.2f}")
        table.add_row("Cash", f"${safe_float(row.get('cash')):,.2f}")
        table.add_row("Market Value", f"${safe_float(row.get('market_val')):,.2f}")
        table.add_row("Realized P&L", f"${safe_float(row.get('realized_pl')):,.2f}")
        table.add_row("Unrealized P&L", f"${safe_float(row.get('unrealized_pl')):,.2f}")
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
        table.add_column("Diluted Cost", justify="right", style="dim")
        table.add_column("Avg Price", justify="right", style="bold")
        table.add_column("Price", justify="right")
        table.add_column("Market Val", justify="right")
        table.add_column("P&L", justify="right")
        table.add_column("P&L %", justify="right")

        for _, row in data.iterrows():
            code = str(row.get('code', 'N/A'))
            name = str(row.get('stock_name', 'N/A'))
            qty = safe_float(row.get('qty'))
            cost = safe_float(row.get('cost_price'))
            avg_cost = safe_float(row.get('average_cost'))
            price = safe_float(row.get('nominal_price'))
            mkt_val = safe_float(row.get('market_val'))
            pl_val = safe_float(row.get('pl_val'))
            pl_ratio = safe_float(row.get('pl_ratio'))

            pl_style = "green" if pl_val >= 0 else "red"
            
            table.add_row(
                code,
                name,
                f"{qty:,.0f}",
                f"{cost:,.2f}",
                f"{avg_cost:,.2f}",
                f"{price:,.2f}",
                f"{mkt_val:,.2f}",
                f"[{pl_style}]{pl_val:+,.2f}[/{pl_style}]",
                f"[{pl_style}]{pl_ratio:+.2f}%[/{pl_style}]"
            )
        
        console.print(table)
    else:
        console.print("[yellow]No positions found (Empty portfolio).[/yellow]")

    ConnectionManager.close()

# --- 修改后的 get_statement 函数 ---
def get_statement(date_str=None):
    """
    Fetches a statement (Deals + Cash Flow) for a specific date or date range.
    date_str format: 'YYMMDD' or 'YYMMDD-YYMMDD'.
    """
    ctx = ConnectionManager.get_trade_context()
    market_tz = get_market_timezone()
    
    start_date = None
    end_date = None
    query_label = ""
    date_list = []

    # 1. 解析日期或日期范围
    if date_str:
        try:
            if '-' in date_str:
                # 处理范围: YYMMDD-YYMMDD
                parts = date_str.split('-')
                if len(parts) != 2:
                    console.print(f"[bold red]Invalid range format:[/bold red] {date_str}. Use YYMMDD-YYMMDD.")
                    return
                
                s_obj = datetime.strptime(parts[0], "%y%m%d")
                e_obj = datetime.strptime(parts[1], "%y%m%d")
                
                if s_obj > e_obj:
                     console.print(f"[bold red]Start date must be before end date.[/bold red]")
                     return
                     
                start_date = s_obj.strftime("%Y-%m-%d")
                end_date = e_obj.strftime("%Y-%m-%d")
                query_label = f"{start_date} to {end_date}"
                
                # 生成所有需要查询的日期列表 (用于 Cash Flow)
                curr = s_obj
                while curr <= e_obj:
                    date_list.append(curr.strftime("%Y-%m-%d"))
                    curr += timedelta(days=1)
                    
            else:
                # 处理单日: YYMMDD
                dt = datetime.strptime(date_str, "%y%m%d")
                start_date = dt.strftime("%Y-%m-%d")
                end_date = start_date
                query_label = start_date
                date_list = [start_date]
                
        except ValueError:
            console.print(f"[bold red]Invalid date format:[/bold red] {date_str}. Use YYMMDD or YYMMDD-YYMMDD.")
            return
    else:
        # 默认查询今天
        today = datetime.now(market_tz).strftime("%Y-%m-%d")
        start_date = today
        end_date = today
        query_label = today
        date_list = [today]

    console.print(f"[dim]Generating statement for [bold white]{query_label}[/bold white]...[/dim]")

    # 2. 查询交易 (Deals) - API 支持范围查询
    ret_deals, data_deals = ctx.history_deal_list_query(
        start=start_date, end=end_date, trd_env=TRADING_ENV
    )

    # 3. 查询资金流水 (Cash Flow) - API 需要单日循环
    all_cash_flows = []
    
    # 使用 rich 的 status 显示加载动画，防止循环太久用户以为卡死
    with console.status(f"[dim]Fetching cash flows for {len(date_list)} days...[/dim]"):
        for d in date_list:
            r, d_data = ctx.get_acc_cash_flow(clearing_date=d, trd_env=TRADING_ENV)
            if r == RET_OK and not d_data.empty:
                all_cash_flows.append(d_data)
    
    data_flow = pd.DataFrame()
    ret_flow = RET_OK
    if all_cash_flows:
        data_flow = pd.concat(all_cash_flows, ignore_index=True)
        # 按时间排序
        if 'create_time' in data_flow.columns:
             data_flow = data_flow.sort_values(by='create_time')
        # 如果是老版本只有 pay_time，可以尝试按 pay_time 排
        elif 'pay_time' in data_flow.columns:
             data_flow = data_flow.sort_values(by='pay_time')

    # 4. 查询费用 (Fees)
    fees_map = {} 
    if ret_deals == RET_OK and not data_deals.empty:
        order_ids = list(set(data_deals['order_id'].tolist()))
        # API 限制一次查太多可能会报错，通常几百个没问题。
        # 如果范围很大，建议分批查询 (这里暂且假设日内或短周期交易量不超限)
        ret_fee, data_fee = ctx.order_fee_query(order_id_list=order_ids, trd_env=TRADING_ENV)
        
        if ret_fee == RET_OK and not data_fee.empty:
            for _, row in data_fee.iterrows():
                oid = row.get('order_id')
                amt = safe_float(row.get('fee_amount'))
                if oid in fees_map:
                    fees_map[oid] += amt
                else:
                    fees_map[oid] = amt

    # --- 显示交易记录 (Deals) ---
    total_fees_period = 0.0
    
    if ret_deals == RET_OK and not data_deals.empty:
        # 按时间倒序或正序显示
        if 'create_time' in data_deals.columns:
            data_deals = data_deals.sort_values(by='create_time', ascending=True)
            
        deal_table = Table(title=f"Executed Trades ({query_label})", style="blue")
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
            amount = price * qty
            
            order_id = row.get('order_id')
            fee_display = "-"
            
            if order_id in fees_map:
                fee_val = fees_map[order_id]
                # 只是为了显示美观，对于同一个订单的多笔成交，只在第一笔显示总费用
                if order_id not in processed_orders:
                    fee_display = f"{fee_val:.2f}"
                    total_fees_period += fee_val
                    processed_orders.add(order_id)
                else:
                    fee_display = "(see above)"

            deal_table.add_row(
                str(row.get('create_time', 'N/A')), # 显示完整时间
                f"[{color}]{side}[/{color}]",
                str(row.get('code', 'N/A')),
                f"{price:,.2f}",
                f"{qty:,.0f}",
                f"{amount:,.2f}",
                fee_display
            )
        console.print(deal_table)
        console.print(f"[dim right]Total Fees for period: ${total_fees_period:.2f}[/dim right]")
    else:
        console.print(Panel(f"No trades executed during {query_label}.", title="Trades", style="dim"))

    # --- 显示资金流水 (Cash Flow) ---
    if not data_flow.empty:
        flow_table = Table(title=f"Cash Flow / Settlements ({query_label})", style="magenta")
        flow_table.add_column("Time", style="dim")
        flow_table.add_column("Type")
        flow_table.add_column("Amount", justify="right")
        flow_table.add_column("Description", style="dim")

        for _, row in data_flow.iterrows():
            amt = safe_float(row.get('cash_flow_amount', 0))
            color = "green" if amt >= 0 else "red"
            time_val = str(row.get('create_time', row.get('pay_time', 'N/A')))
            
            flow_table.add_row(
                time_val,
                str(row.get('cash_flow_name', 'Unknown')),
                f"[{color}]{amt:,.2f}[/{color}]",
                str(row.get('cash_flow_remark', '')) 
            )
        console.print(flow_table)
    else:
        console.print(Panel(f"No cash flow settled during {query_label}.", title="Cash Flow", style="dim"))

    ConnectionManager.close()