import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from moomoo import RET_OK, SubType
# Modified: Import helpers from connection
from connection import ConnectionManager, normalize_ticker, safe_float

console = Console()

def get_stock_quote(ticker):
    """
    Fetches and displays Quote and Level-2 Order Book for a stock.
    """
    # Use shared normalization
    code = normalize_ticker(ticker)
    ctx = ConnectionManager.get_quote_context()

    console.print(f"[dim]Fetching data for {code}...[/dim]")

    # 1. Subscribe to QUOTE and ORDER_BOOK
    ret_sub, err_message = ctx.subscribe([code], [SubType.QUOTE, SubType.ORDER_BOOK])
    
    if ret_sub != RET_OK:
        console.print(f"[bold red]Subscription failed:[/bold red] {err_message}")
        ConnectionManager.close()
        return

    # 2. Fetch Basic Quote
    ret_quote, data_quote = ctx.get_stock_quote([code])
    
    # 3. Fetch Order Book
    ret_book, data_book = ctx.get_order_book(code)

    if ret_quote != RET_OK:
        console.print(f"[bold red]Error fetching quote:[/bold red] {data_quote}")
        ConnectionManager.close()
        return

    # --- Display Logic ---
    
    # A. Display Basic Quote Info
    if not data_quote.empty:
        q = data_quote.iloc[0]
        
        # Use safe_float for robustness
        last_price = safe_float(q.get('last_price'))
        open_price = safe_float(q.get('open_price'))
        high_price = safe_float(q.get('high_price'))
        low_price = safe_float(q.get('low_price'))
        prev_close = safe_float(q.get('prev_close_price'))
        volume = safe_float(q.get('volume'))

        color = "green" if last_price >= open_price else "red"
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)
        
        grid.add_row(
            f"[bold {color}]Last: {last_price}[/]", 
            f"High: {high_price}", 
            f"Low: {low_price}"
        )
        grid.add_row(
            f"Vol: {volume:,.0f}", 
            f"Open: {open_price}", 
            f"Prev Cls: {prev_close}"
        )

        console.print(Panel(grid, title=f"[bold gold1]{code}[/] Quote", subtitle=str(q.get('data_time'))))

    # B. Display Level 2 Order Book
    if ret_book == RET_OK and data_book is not None:
        bids = data_book.get('Bid', [])
        asks = data_book.get('Ask', [])
        
        bid_table = Table(title="Bid (Buy)", style="green", box=None)
        bid_table.add_column("Vol", justify="right")
        bid_table.add_column("Price", justify="right", style="bold green")

        ask_table = Table(title="Ask (Sell)", style="red", box=None)
        ask_table.add_column("Price", justify="left", style="bold red")
        ask_table.add_column("Vol", justify="left")

        limit = 10
        for i in range(limit):
            if i < len(bids):
                item = bids[i]
                b_price = safe_float(item[0])
                b_vol = safe_float(item[1])
                bid_table.add_row(f"{b_vol:,.0f}", f"{b_price:.2f}")
            else:
                bid_table.add_row("-", "-")
                
            if i < len(asks):
                item = asks[i]
                a_price = safe_float(item[0])
                a_vol = safe_float(item[1])
                ask_table.add_row(f"{a_price:.2f}", f"{a_vol:,.0f}")
            else:
                ask_table.add_row("-", "-")

        console.print(Columns([bid_table, ask_table]))
    else:
        console.print("[yellow]Order book not available (Check permissions or market status).[/yellow]")

    ConnectionManager.close()