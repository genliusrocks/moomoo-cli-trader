import click
from rich.console import Console
from rich.table import Table  # Added Table import
from moomoo import TrdSide, OrderType, RET_OK
from connection import ConnectionManager, TRADING_ENV

console = Console()

def get_orders():
    """
    Fetches and displays a list of orders (Open & Recently Ended).
    """
    ctx = ConnectionManager.get_trade_context()
    console.print(f"[dim]Fetching orders for {TRADING_ENV}...[/dim]")

    # Fetch orders (returns all orders for the environment by default)
    ret, data = ctx.order_list_query(trd_env=TRADING_ENV)

    if ret != RET_OK:
        console.print(f"[bold red]Error fetching orders:[/bold red] {data}")
        ConnectionManager.close()
        return

    if data.empty:
        console.print("[yellow]No orders found.[/yellow]")
        ConnectionManager.close()
        return

    # Sort by update time descending (newest first)
    if 'updated_time' in data.columns:
        data = data.sort_values(by='updated_time', ascending=False)

    # Create Table
    table = Table(title=f"Order Book ({TRADING_ENV})")
    table.add_column("Order ID", style="cyan", no_wrap=True)
    table.add_column("Symbol", style="bold yellow")
    table.add_column("Side", style="bold")
    table.add_column("Status")
    table.add_column("Price", justify="right")
    table.add_column("Qty", justify="right")
    table.add_column("Filled", justify="right")
    table.add_column("Time", style="dim")

    for _, row in data.iterrows():
        # Formatting
        oid = str(row.get('order_id', 'N/A'))
        code = str(row.get('code', 'N/A'))
        side = str(row.get('trd_side', 'N/A'))
        status = str(row.get('order_status', 'N/A'))
        price = row.get('price', 0.0)
        qty = row.get('qty', 0.0)
        filled = row.get('dealt_qty', 0.0)
        updated_time = str(row.get('updated_time', ''))

        # Color coding logic
        side_style = "green" if "BUY" in side.upper() else "red"
        
        status_style = "white"
        if status in ['SUBMITTED', 'FILLED_PART', 'WAITING_SUBMIT']:
            status_style = "bold green" # Active/Working
        elif status == 'FILLED_ALL':
            status_style = "blue"       # Completed
        elif status in ['CANCELLED_ALL', 'CANCELLED_PART', 'FAILED']:
            status_style = "dim red"    # Dead

        table.add_row(
            oid,
            code,
            f"[{side_style}]{side}[/{side_style}]",
            f"[{status_style}]{status}[/{status_style}]",
            f"{price:.2f}",
            f"{qty:.0f}",
            f"{filled:.0f}",
            updated_time
        )
    
    console.print(table)
    ConnectionManager.close()

def place_trade(ticker, side, order_type_str, price, qty):
    """
    Executes a trade order (Buy or Sell).
    """
    ctx = ConnectionManager.get_trade_context()
    
    # 1. Normalize Ticker
    code = ticker.upper()
    if "." not in code:
        code = f"US.{code}"
    
    # 2. Map Side
    trd_side = TrdSide.BUY if side.lower() == 'buy' else TrdSide.SELL
    
    # 3. Map Order Type
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

    # 4. Place Order
    ret, data = ctx.place_order(
        price=price, 
        qty=qty, 
        code=code, 
        trd_side=trd_side, 
        order_type=order_type, 
        trd_env=TRADING_ENV
    )

    # 5. Handle Result
    if ret == RET_OK:
        order_id = data['order_id'][0]
        console.print(f"[bold green]Order Placed Successfully![/bold green]")
        console.print(f"Order ID: {order_id}")
    else:
        console.print(f"[bold red]Order Failed:[/bold red] {data}")
        if "lock" in str(data).lower():
            console.print("[dim]Tip: Use 'python main.py unlock <password>' first.[/dim]")

    ConnectionManager.close()