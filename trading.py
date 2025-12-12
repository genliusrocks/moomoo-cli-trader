import click
from rich.console import Console
from rich.table import Table
from moomoo import TrdSide, OrderType, OrderStatus, RET_OK, ModifyOrderOp, TrailType
# 确保 connection.py 已经包含 safe_float 和 normalize_ticker
from connection import ConnectionManager, TRADING_ENV, safe_float, normalize_ticker

console = Console()

# Mapping CLI strings to Moomoo OrderType Enums
ORDER_TYPE_MAP = {
    'LIMIT': OrderType.NORMAL,
    'MARKET': OrderType.MARKET,
    'STOP': OrderType.STOP,
    'STOP_LIMIT': OrderType.STOP_LIMIT,
    'MIT': OrderType.MARKET_IF_TOUCHED,      # Market If Touched
    'LIT': OrderType.LIMIT_IF_TOUCHED,       # Limit If Touched
    'TR_STOP': OrderType.TRAILING_STOP,      # Trailing Stop
    'TR_STOP_LIMIT': OrderType.TRAILING_STOP_LIMIT # Trailing Stop Limit
}

def get_orders():
    """
    Fetches and displays the list of orders for today.
    """
    ctx = ConnectionManager.get_trade_context()
    console.print(f"[dim]Fetching orders for {TRADING_ENV}...[/dim]")

    # Fetch orders
    ret, data = ctx.order_list_query(trd_env=TRADING_ENV)

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching orders:[/bold red] {data}")
        ConnectionManager.close()
        return

    if not data.empty:
        # Sort by updated_time descending
        if 'updated_time' in data.columns:
            data = data.sort_values(by='updated_time', ascending=False)

        table = Table(title=f"Order Book ({TRADING_ENV})")

        table.add_column("Order ID", style="dim")
        table.add_column("Symbol", style="yellow")
        table.add_column("Side", justify="center")
        table.add_column("Status")
        table.add_column("Price", justify="right")
        table.add_column("Filled Px", justify="right", style="bold cyan")
        table.add_column("Qty", justify="right")
        table.add_column("Filled", justify="right")
        # 新增 Trigger 列，用于显示 aux_price
        table.add_column("Trigger", justify="right", style="magenta") 
        table.add_column("Time", justify="right", style="dim")

        for _, row in data.iterrows():
            side = row.get('trd_side', 'UNKNOWN')
            side_style = "bold red" if side == "BUY" else "bold green"
            
            status = row.get('order_status', 'UNKNOWN')
            status_style = "green" if status in [OrderStatus.FILLED_ALL, OrderStatus.FILLED_PART] else "white"
            if status in [OrderStatus.CANCELLED_ALL, OrderStatus.CANCELLED_PART]:
                status_style = "dim"
            elif status == OrderStatus.FAILED:
                status_style = "red"

            order_id = str(row.get('order_id', ''))
            code = str(row.get('code', ''))
            price = safe_float(row.get('price'))
            dealt_avg_price = safe_float(row.get('dealt_avg_price'))
            qty = safe_float(row.get('qty'))
            dealt_qty = safe_float(row.get('dealt_qty'))
            update_time = str(row.get('updated_time', ''))
            
            # 获取触发价 (Aux Price)
            aux_price = safe_float(row.get('aux_price'))
            # 如果有触发价则显示，否则显示 "-"
            aux_display = f"{aux_price:.2f}" if aux_price > 0 else "-"

            filled_price_display = f"{dealt_avg_price:.2f}"
            if dealt_qty == 0:
                filled_price_display = "-"

            table.add_row(
                order_id,
                code,
                f"[{side_style}]{side}[/{side_style}]",
                f"[{status_style}]{status}[/{status_style}]",
                f"{price:.2f}",
                filled_price_display,
                f"{qty:.0f}",
                f"{dealt_qty:.0f}",
                aux_display, # 显示触发价
                update_time
            )

        console.print(table)
    else:
        console.print("[yellow]No orders found.[/yellow]")

    ConnectionManager.close()

def place_trade(ticker, side, order_type_str, price, qty, 
                aux_price=0.0, trail_type=None, trail_value=0.0, trail_spread=0.0):
    """
    Executes a trade order with support for advanced order types.
    """
    ctx = ConnectionManager.get_trade_context()
    
    code = normalize_ticker(ticker)
    trd_side = TrdSide.BUY if side.lower() == 'buy' else TrdSide.SELL
    
    # 1. Map CLI String to Enum
    order_type_enum = ORDER_TYPE_MAP.get(order_type_str.upper())
    if not order_type_enum:
        console.print(f"[bold red]Invalid order type:[/bold red] {order_type_str}")
        return

    # 2. Validate Parameters
    # Limit Orders need Price
    if order_type_enum in [OrderType.NORMAL, OrderType.STOP_LIMIT, OrderType.LIMIT_IF_TOUCHED] and price <= 0:
        console.print("[bold red]Error:[/bold red] This order type requires a limit PRICE.")
        return
    
    # Trigger Orders need Aux Price (Stop/MIT/LIT)
    if order_type_enum in [OrderType.STOP, OrderType.STOP_LIMIT, OrderType.MARKET_IF_TOUCHED, OrderType.LIMIT_IF_TOUCHED]:
        if aux_price <= 0:
            console.print(f"[bold red]Error:[/bold red] {order_type_str} requires --aux (Trigger/Stop Price).")
            return

    # Trailing Orders need Trail Value
    moomoo_trail_type = TrailType.NONE
    if order_type_enum in [OrderType.TRAILING_STOP, OrderType.TRAILING_STOP_LIMIT]:
        if trail_value <= 0:
            console.print(f"[bold red]Error:[/bold red] {order_type_str} requires --trail (Trailing Amount/Ratio).")
            return
        
        if trail_type and trail_type.lower() == 'ratio':
            moomoo_trail_type = TrailType.RATIO
        else:
            moomoo_trail_type = TrailType.AMOUNT

    console.print(f"[yellow]Placing order...[/yellow]")
    console.print(f"Side: [bold]{trd_side}[/bold] | Symbol: [bold cyan]{code}[/bold cyan]")
    console.print(f"Type: {order_type_str.upper()} | Qty: {qty}")
    if price > 0: console.print(f"Limit Price: {price}")
    if aux_price > 0: console.print(f"Trigger Price: {aux_price}")
    if trail_value > 0: console.print(f"Trailing: {trail_value} ({moomoo_trail_type})")

    # 3. Call API
    ret, data = ctx.place_order(
        price=price, 
        qty=qty, 
        code=code, 
        trd_side=trd_side, 
        order_type=order_type_enum, 
        trd_env=TRADING_ENV,
        # Advanced Params
        aux_price=aux_price,       # For STOP, MIT, LIT
        trail_type=moomoo_trail_type, 
        trail_value=trail_value,   # For Trailing
        trail_spread=trail_spread  # For Trailing Stop Limit
    )

    if ret == RET_OK:
        order_id = data['order_id'][0]
        console.print(f"[bold green]Order Placed Successfully![/bold green]")
        console.print(f"Order ID: {order_id}")
    else:
        console.print(f"[bold red]Order Failed:[/bold red] {data}")
        if "lock" in str(data).lower():
            console.print("[dim]Tip: Use 'python main.py unlock <password>' first.[/dim]")

    ConnectionManager.close()

def cancel_order(order_id):
    """
    Cancels an order by ID.
    """
    ctx = ConnectionManager.get_trade_context()
    console.print(f"[yellow]Cancelling order {order_id}...[/yellow]")

    ret, data = ctx.modify_order(
        ModifyOrderOp.CANCEL, 
        order_id, 
        0, 
        0, 
        trd_env=TRADING_ENV
    )

    if ret == RET_OK:
        console.print(f"[bold green]Order {order_id} Cancelled Successfully![/bold green]")
    else:
        console.print(f"[bold red]Failed to Cancel:[/bold red] {data}")
    
    ConnectionManager.close()