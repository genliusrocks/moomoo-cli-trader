import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from moomoo import RET_OK, SubType
# Removed 'OrderBook' import
from connection import ConnectionManager

console = Console()

def normalize_ticker(ticker):
    """
    Ensures ticker has a market prefix. Defaults to 'US.' if missing.
    """
    ticker = ticker.upper()
    if "." not in ticker:
        return f"US.{ticker}"
    return ticker

def get_stock_quote(ticker):
    """
    Fetches and displays Quote and Level-2 Order Book for a stock.
    """
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
        
        last_price = q.get('last_price', 0.0)
        open_price = q.get('open_price', 0.0)
        color = "green" if last_price >= open_price else "red"
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)
        
        grid.add_row(
            f"[bold {color}]Last: {last_price}[/]", 
            f"High: {q.get('high_price')}", 
            f"Low: {q.get('low_price')}"
        )
        grid.add_row(
            f"Vol: {q.get('volume'):,}", 
            f"Open: {open_price}", 
            f"Prev Cls: {q.get('prev_close_price')}"
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
                # Safe unpacking: API returns (price, vol, count, details)
                item = bids[i]
                bid_table.add_row(f"{item[1]:,}", f"{item[0]:.2f}")
            else:
                bid_table.add_row("-", "-")
                
            if i < len(asks):
                item = asks[i]
                ask_table.add_row(f"{item[0]:.2f}", f"{item[1]:,}")
            else:
                ask_table.add_row("-", "-")

        console.print(Columns([bid_table, ask_table]))
    else:
        console.print("[yellow]Order book not available (Check permissions or market status).[/yellow]")

    ConnectionManager.close()