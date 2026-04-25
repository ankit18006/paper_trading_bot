# Paper Trading Bot — No API Key Required

A Python CLI paper trading bot that simulates orders using **live Binance public market prices**. No API key, no account, no credentials needed.

---

## How it works

| What | How |
|---|---|
| Live prices | Binance public REST API (`/api/v3/ticker`) — no auth |
| Order execution | Simulated in-memory with a JSON state file |
| MARKET orders | Fill instantly at live price |
| LIMIT orders | Go to OPEN, fill when price crosses your level |
| STOP_MARKET orders | Trigger when price reaches the stop level |
| State persistence | Saved to `paper_state.json` between runs |
| Starting balance | $10,000 USDT |

---

## Project Structure

```
paper_trading_bot/
├── bot/
│   ├── __init__.py
│   ├── cli.py            # CLI entry point (argparse)
│   ├── market.py         # Binance public API (no key needed)
│   ├── paper_engine.py   # Simulated order + P&L engine
│   ├── validators.py     # Input validation
│   └── logging_config.py
├── logs/
│   └── trading_bot_YYYYMMDD.log
├── paper_state.json      # Auto-created on first order
├── requirements.txt
└── README.md
```

---

## Setup

```bash
git clone <your-repo-url>
cd paper_trading_bot

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

No `.env` file needed. No API keys.

---

## Commands

### Show live price

```bash
python -m bot.cli price --symbol BTCUSDT
```

```
  BTCUSDT Live Market Data
  ──────────────────────────────────────────
  Last Price   : $95,312.40
  24h Change   : ▲ +2.48%
  24h High     : $96,000.00
  24h Low      : $93,100.00
```

### Place a MARKET order

```bash
python -m bot.cli order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a LIMIT order

```bash
python -m bot.cli order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 90000
```

### Place a STOP_MARKET order

```bash
python -m bot.cli order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 92000
```

### View portfolio and P&L

```bash
python -m bot.cli portfolio
```

### List all orders

```bash
python -m bot.cli orders
```

### Check open orders (fill any that triggered)

```bash
python -m bot.cli check --symbol BTCUSDT
```

### Cancel an open order

```bash
python -m bot.cli cancel --id 3
```

### Reset account to $10,000

```bash
python -m bot.cli reset
```

---

## Sample Output

```
  ORDER CONFIRMATION
  ──────────────────────────────────────────
  Order ID     : #1
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Status       : FILLED
  Quantity     : 0.001
  Exec Price   : $95,318.70
  Order Value  : $95.32 USDT
  Filled At    : 2025-01-15 11:01:15
  ──────────────────────────────────────────
  ✓ Order FILLED!
```

---

## Assumptions

- Uses Binance **spot** public ticker (`api.binance.com`) for live prices — no futures testnet needed
- Open orders are checked manually via `python -m bot.cli check` (no background watcher)
- State persists in `paper_state.json`; delete it or run `reset` to start fresh
- No leverage simulation (1x only)

---

## Dependencies

```
requests>=2.31.0
```

No Binance SDK. No API key. Just `requests` and live public prices.


## Sample Logs (Live Render Deployment)

### MARKET Order — BUY FILLED

2026-04-25 08:17:20 | INFO | cli | Command: order
2026-04-25 08:17:20 | INFO | market | Live price for BTCUSDT: $77561.15
2026-04-25 08:17:20 | INFO | paper_engine | Order #1 FILLED | BUY MARKET 0.0010 BTCUSDT @ $77561.15 | cost=$77.56
✓ Order FILLED



### LIMIT Order — SELL OPEN
2026-04-25 08:24:13 | INFO | cli | Command: order
2026-04-25 08:24:13 | INFO | market | Live price for BTCUSDT: $77555.87
2026-04-25 08:24:13 | INFO | paper_engine | Limit order #1 placed OPEN @ $85000.00 (live=$77555.87)
⏳ Order OPEN!


