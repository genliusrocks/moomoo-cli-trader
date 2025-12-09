import click
from rich.console import Console
from moomoo import TrdSide, OrderType, RET_OK
from connection import ConnectionManager, TRADING_ENV

console = Console()

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
    # This logic handles both 'buy' and 'sell' strings
    trd_side = TrdSide.BUY if side.lower() == 'buy' else TrdSide.SELL
    
    # 3. Map Order Type
    if order_type_str.lower() == 'market':
        order_type = OrderType.MARKET
    else:
        order_type = OrderType.NORMAL # Limit Order
        
    console.print(f"[yellow]Placing order...[/yellow]")
    console.print(f"Side: [bold]{trd_side}[/bold]") # Will print TrdSide.BUY or TrdSide.SELL
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