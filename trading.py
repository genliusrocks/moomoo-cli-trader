import click
from rich.console import Console
from rich.table import Table
from moomoo import TrdSide, OrderType, OrderStatus, RET_OK, ModifyOrderOp
# Modified: Import helpers
from connection import ConnectionManager, TRADING_ENV, safe_float, normalize_ticker

console = Console()

def get_orders():
    """
    Fetches and displays the list of orders for today.
    """
    ctx = ConnectionManager.get_trade_context()
    console.print(f"[dim]Fetching orders for {TRADING_ENV}...[/dim]")

    # Fetch orders (filters can be added if needed)
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
        table.add_column("Filled Price", justify="right", style="bold cyan")
        table.add_column("Qty", justify="right")
        table.add_column("Filled", justify="right")
        table.add_column("Time", justify="right", style="dim")

        for _, row in data.iterrows():
            # Side Color
            side = row.get('trd_side', 'UNKNOWN')
            side_style = "bold red" if side == "BUY" else "bold green"
            
            # Status Color
            status = row.get('order_status', 'UNKNOWN')
            status_style = "green" if status in [OrderStatus.FILLED_ALL, OrderStatus.FILLED_PART] else "white"
            if status in [OrderStatus.CANCELLED_ALL, OrderStatus.CANCELLED_PART]:
                status_style = "dim"
            elif status == OrderStatus.FAILED:
                status_style = "red"

            # Fields using safe_float
            order_id = str(row.get('order_id', ''))
            code = str(row.get('code', ''))
            price = safe_float(row.get('price'))
            dealt_avg_price = safe_float(row.get('dealt_avg_price'))
            qty = safe_float(row.get('qty'))
            dealt_qty = safe_float(row.get('dealt_qty'))
            update_time = str(row.get('updated_time', ''))

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
                update_time
            )

        console.print(table)
    else:
        console.print("[yellow]No orders found.[/yellow]")

    ConnectionManager.close()

def place_trade(ticker, side, order_type_str, price, qty):
    """
    Executes a trade order (Buy or Sell).
    """
    ctx = ConnectionManager.get_trade_context()
    
    # Use helper
    code = normalize_ticker(ticker)
    
    trd_side = TrdSide.BUY if side.lower() == 'buy' else TrdSide.SELL
    
    if order_type_str.lower() == 'market':
        order_type = OrderType.MARKET
    else:
        order_type = OrderType.NORMAL # Limit Order
        
    console.print(f"[yellow]Placing order...[/yellow]")
    console.print(f"Side: [bold]{trd_side}[/bold]")
    console.print(f"Symbol: [bold cyan]{code}[/bold cyan]")
    console.print(f"Type: {order_type}")
    console.print(f"Price: {price}")
    console.print(f"Qty: {qty}")

    ret, data = ctx.place_order(
        price=price, 
        qty=qty, 
        code=code, 
        trd_side=trd_side, 
        order_type=order_type, 
        trd_env=TRADING_ENV
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