"""
paper_engine.py — In-memory paper trading engine.

Simulates order placement, fill logic, and P&L tracking using
live Binance prices. No API key required.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional

from bot.market import get_ticker_price
from bot.logging_config import setup_logger

logger = setup_logger("paper_engine")

STATE_FILE = "paper_state.json"
STARTING_BALANCE = 10_000.0  # USDT


@dataclass
class Order:
    order_id: int
    symbol: str
    side: str            # BUY | SELL
    order_type: str      # MARKET | LIMIT | STOP_MARKET
    quantity: float
    price: Optional[float]       # limit price
    stop_price: Optional[float]  # stop trigger
    status: str          # OPEN | FILLED | CANCELLED
    exec_price: Optional[float] = None
    filled_at: Optional[str] = None
    pnl: float = 0.0


@dataclass
class PaperAccount:
    balance: float = STARTING_BALANCE
    orders: List[Order] = field(default_factory=list)
    _next_id: int = 1

    def next_id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i


_account = PaperAccount()


def _load_state():
    global _account
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
            _account.balance = data.get("balance", STARTING_BALANCE)
            _account._next_id = data.get("next_id", 1)
            _account.orders = [Order(**o) for o in data.get("orders", [])]
            logger.debug("Loaded paper state: balance=%.2f, orders=%d", _account.balance, len(_account.orders))
        except Exception as e:
            logger.warning("Could not load state: %s. Starting fresh.", e)


def _save_state():
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({
                "balance": _account.balance,
                "next_id": _account._next_id,
                "orders": [asdict(o) for o in _account.orders],
            }, f, indent=2)
    except Exception as e:
        logger.warning("Could not save state: %s", e)


def place_paper_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Order:
    """
    Simulate placing an order. MARKET orders fill instantly at live price.
    LIMIT and STOP_MARKET go to OPEN status until check_open_orders() fills them.
    """
    live_price = get_ticker_price(symbol)

    order = Order(
        order_id=_account.next_id(),
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        status="OPEN",
    )

    if order_type == "MARKET":
        _fill_order(order, live_price)
    elif order_type == "LIMIT":
        # Immediately fill if market is already at or past the limit
        if (side == "BUY" and live_price <= price) or (side == "SELL" and live_price >= price):
            _fill_order(order, price)
        else:
            logger.info("Limit order #%d placed OPEN @ $%.2f (live=$%.2f)", order.order_id, price, live_price)
    elif order_type == "STOP_MARKET":
        if (side == "BUY" and live_price >= stop_price) or (side == "SELL" and live_price <= stop_price):
            _fill_order(order, live_price)
        else:
            logger.info("Stop order #%d placed OPEN, trigger=$%.2f (live=$%.2f)", order.order_id, stop_price, live_price)

    _account.orders.append(order)
    _save_state()
    return order


def _fill_order(order: Order, exec_price: float):
    cost = order.quantity * exec_price
    if order.side == "BUY":
        if cost > _account.balance:
            raise ValueError(
                f"Insufficient balance. Need ${cost:.2f}, have ${_account.balance:.2f}"
            )
        _account.balance -= cost
    order.exec_price = exec_price
    order.status = "FILLED"
    order.filled_at = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(
        "Order #%d FILLED | %s %s %.4f %s @ $%.2f | cost=$%.2f",
        order.order_id, order.side, order.order_type, order.quantity,
        order.symbol, exec_price, cost,
    )


def check_open_orders(symbol: str) -> List[Order]:
    """Poll open orders and fill any that have hit their trigger price."""
    open_orders = [o for o in _account.orders if o.status == "OPEN" and o.symbol == symbol]
    if not open_orders:
        return []

    live_price = get_ticker_price(symbol)
    filled = []

    for order in open_orders:
        if order.order_type == "LIMIT":
            if (order.side == "BUY" and live_price <= order.price) or \
               (order.side == "SELL" and live_price >= order.price):
                _fill_order(order, order.price)
                filled.append(order)
        elif order.order_type == "STOP_MARKET":
            if (order.side == "BUY" and live_price >= order.stop_price) or \
               (order.side == "SELL" and live_price <= order.stop_price):
                _fill_order(order, live_price)
                filled.append(order)

    if filled:
        _save_state()
    return filled


def get_portfolio_summary(symbol: str = "BTCUSDT") -> dict:
    """Return account summary with live P&L on filled orders."""
    live_price = get_ticker_price(symbol)
    filled = [o for o in _account.orders if o.status == "FILLED" and o.symbol == symbol]
    total_pnl = 0.0
    for o in filled:
        if o.side == "BUY":
            o.pnl = (live_price - o.exec_price) * o.quantity
        else:
            o.pnl = (o.exec_price - live_price) * o.quantity
        total_pnl += o.pnl

    return {
        "symbol": symbol,
        "live_price": live_price,
        "balance_usdt": _account.balance,
        "total_pnl": total_pnl,
        "open_orders": len([o for o in _account.orders if o.status == "OPEN"]),
        "filled_orders": len(filled),
        "all_orders": _account.orders,
    }


def cancel_order(order_id: int) -> Optional[Order]:
    for o in _account.orders:
        if o.order_id == order_id and o.status == "OPEN":
            o.status = "CANCELLED"
            logger.info("Order #%d CANCELLED", order_id)
            _save_state()
            return o
    return None


def reset_account():
    global _account
    _account = PaperAccount()
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    logger.info("Paper account reset. Balance restored to $%.2f", STARTING_BALANCE)


# Load saved state on import
_load_state()
