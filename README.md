# moomoo-cli-trader

**moomoo-cli-trader** is a lightweight, terminal-based trading tool built on the Moomoo (Futu) Open API. It allows developers and power users to execute orders, monitor real-time positions, and track account assets directly from the shell without the need for a heavy GUI.


## Features

* **Terminal Dashboard:** View real-time account assets, P&L, and market value using a rich terminal interface.
* **Order Management:** Place market and limit orders for Stocks and ETFs directly from the CLI.
* **Position Monitoring:** List current positions with real-time quote updates.
* **Market Data:** Fetch real-time quotes and snapshots for specific tickers.
* **Secure Connection:** Connects via the local Moomoo OpenD gateway.

## Prerequisites

Before running this tool, you must have the following installed and running:

1.  **Moomoo OpenD (Gateway):**
    * Download the Moomoo OpenD (or Futu OpenD) gateway from the [official website](https://openapi.moomoo.com/moomoo-api-doc/en/intro/intro.html).
    * Install and run OpenD on your local machine.
    * Log in with your Moomoo credentials.
    * Ensure it is listening on a local port (default is `11111`).

2.  **Python 3.8+**

## Installation

1.  Clone this repository:
    ```bash
    git clone [https://github.com/genliusrocks/moomoo-cli-trader.git](https://github.com/genliusrocks/moomoo-cli-trader.git)
    cd moomoo-cli-trader
    ```

2.  Install dependencies:
    ```bash
    pip install moomoo-api click rich
    ```

## Usage

Ensure **Moomoo OpenD** is running before executing commands.

### 1. View Account Status
Display your current assets, cash, and market value.
```bash
python main.py portfolio --summary
