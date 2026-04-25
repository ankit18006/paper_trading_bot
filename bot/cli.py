"""
cli.py — CLI for the paper trading bot.

All commands use live Binance public prices. No API key required.

Examples:
  python -m bot.cli price --symbol BTCUSDT
  python -m bot.cli order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  python -m bot.cli order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 97000
  python -m bot.cli order --symbol ETHUSDT --side BUY --type STOP_MARKET --quantity 0.01 --stop-price 2000
  python -m bot.cli portfolio
  python -m bot.cli orders
  python -m bot.cli cancel --id 3
  python -m bot.cli reset
"""
from __future__ import annotations

import argparse
import sys

from bot.market import get_24hr_ticker, get_order_book
from bot.paper_engine import (
    place_paper_order, check_open_orders, get_portfolio_summary,
    cancel_order, reset_account,
)
from bot.validators import validate_all, ValidationError
from bot.logging_config import setup_logger

logger = setup_logger("cli")

BANNER = """
  ╔══════════════════════════════════════════╗
  ║  Paper Trading Bot  |  No API Key Needed ║
  ║  Powered by live Binance public prices   ║
  ╚══════════════════════════════════════════╝
"""


def cmd_price(args):
    """Show live price and 24hr stats."""
    data = get_24hr_ticker(args.symbol.upper())
    chg = float(data["priceChangePercent"])
    arrow = "▲" if chg >= 0 else "▼"
    print(f"\n  {args.symbol.upper()} Live Market Data")
    print("  " + "─" * 42)
    print(f"  Last Price   : ${float(data['lastPrice']):,.2f}")
    print(f"  24h Change   : {arrow} {chg:+.2f}%")
    print(f"  24h High     : ${float(data['highPrice']):,.2f}")
    print(f"  24h Low      : ${float(data['lowPrice']):,.2f}")
    print(f"  24h Volume   : {float(data['volume']):,.4f} {args.symbol[:3]}")
    print()


def cmd_order(args):
    """Place a paper order."""
    try:
        params = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as e:
        print(f"\n  ✗ Validation Error: {e}\n")
        sys.exit(2)

    print(f"\n  ORDER REQUEST")
    print("  " + "─" * 42)
    print(f"  Symbol     : {params['symbol']}")
    print(f"  Side       : {params['side']}")
    print(f"  Type       : {params['order_type']}")
    print(f"  Quantity   : {params['quantity']}")
    if params['price']:
        print(f"  Price      : ${params['price']:,.2f}")
    if params['stop_price']:
        print(f"  Stop Price : ${params['stop_price']:,.2f}")
    print("  " + "─" * 42)

    try:
        order = place_paper_order(
            symbol=params['symbol'],
            side=params['side'],
            order_type=params['order_type'],
            quantity=params['quantity'],
            price=params['price'],
            stop_price=params['stop_price'],
        )
    except ValueError as e:
        print(f"\n  ✗ Order rejected: {e}\n")
        sys.exit(3)

    print(f"\n  ORDER CONFIRMATION")
    print("  " + "─" * 42)
    print(f"  Order ID     : #{order.order_id}")
    print(f"  Symbol       : {order.symbol}")
    print(f"  Side         : {order.side}")
    print(f"  Type         : {order.order_type}")
    print(f"  Status       : {order.status}")
    print(f"  Quantity     : {order.quantity}")
    if order.exec_price:
        print(f"  Exec Price   : ${order.exec_price:,.2f}")
        print(f"  Order Value  : ${order.exec_price * order.quantity:,.2f} USDT")
    if order.filled_at:
        print(f"  Filled At    : {order.filled_at}")
    print("  " + "─" * 42)

    icon = "✓" if order.status == "FILLED" else "⏳"
    print(f"\n  {icon} Order {order.status}!\n")


def cmd_portfolio(args):
    """Show account summary and live P&L."""
    summary = get_portfolio_summary(args.symbol.upper())
    pnl = summary['total_pnl']
    pnl_sign = "+" if pnl >= 0 else ""

    print(f"\n  PORTFOLIO SUMMARY  |  {summary['symbol']} @ ${summary['live_price']:,.2f}")
    print("  " + "─" * 42)
    print(f"  Balance (USDT)  : ${summary['balance_usdt']:,.2f}")
    print(f"  Unrealised P&L  : {pnl_sign}${pnl:,.2f}")
    print(f"  Open Orders     : {summary['open_orders']}")
    print(f"  Filled Orders   : {summary['filled_orders']}")
    print()


def cmd_orders(args):
    """List all orders."""
    summary = get_portfolio_summary()
    orders = summary['all_orders']
    if not orders:
        print("\n  No orders placed yet.\n")
        return

    print(f"\n  {'ID':<6} {'Symbol':<10} {'Side':<6} {'Type':<14} {'Qty':<8} {'Price':<12} {'Status':<11} {'P&L'}")
    print("  " + "─" * 78)
    for o in reversed(orders):
        price_str = f"${o.exec_price:,.2f}" if o.exec_price else (f"${o.price:,.2f}" if o.price else f"${o.stop_price:,.2f}" if o.stop_price else "market")
        pnl_str = f"{'+' if o.pnl >= 0 else ''}${o.pnl:.2f}" if o.status == "FILLED" else "—"
        print(f"  #{o.order_id:<5} {o.symbol:<10} {o.side:<6} {o.order_type:<14} {o.quantity:<8.4f} {price_str:<12} {o.status:<11} {pnl_str}")
    print()


def cmd_cancel(args):
    """Cancel an open order by ID."""
    order = cancel_order(args.id)
    if order:
        print(f"\n  ✓ Order #{order.order_id} cancelled.\n")
    else:
        print(f"\n  ✗ Order #{args.id} not found or already filled/cancelled.\n")
        sys.exit(1)


def cmd_check(args):
    """Check open orders and fill any that have triggered."""
    filled = check_open_orders(args.symbol.upper())
    if filled:
        print(f"\n  {len(filled)} order(s) filled:")
        for o in filled:
            print(f"  ✓ #{o.order_id} {o.side} {o.quantity} {o.symbol} @ ${o.exec_price:,.2f}")
    else:
        print(f"\n  No open orders triggered at current price.\n")


def cmd_reset(args):
    """Reset the paper account back to $10,000."""
    confirm = input("  Reset account? All orders will be lost. (yes/no): ").strip().lower()
    if confirm == "yes":
        reset_account()
        print("  ✓ Account reset to $10,000 USDT.\n")
    else:
        print("  Reset cancelled.\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper-bot",
        description="Paper Trading Bot — live Binance prices, no API key required",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # price
    p_price = sub.add_parser("price", help="Show live price and 24hr stats")
    p_price.add_argument("--symbol", "-s", default="BTCUSDT", help="Symbol (default: BTCUSDT)")

    # order
    p_order = sub.add_parser("order", help="Place a paper order")
    p_order.add_argument("--symbol", "-s", required=True)
    p_order.add_argument("--side", required=True, choices=["BUY", "SELL"], type=str.upper)
    p_order.add_argument("--type", dest="order_type", required=True, choices=["MARKET", "LIMIT", "STOP_MARKET"], type=str.upper)
    p_order.add_argument("--quantity", "-q", required=True, type=float)
    p_order.add_argument("--price", "-p", type=float, default=None)
    p_order.add_argument("--stop-price", dest="stop_price", type=float, default=None)

    # portfolio
    p_port = sub.add_parser("portfolio", help="Show account balance and P&L")
    p_port.add_argument("--symbol", default="BTCUSDT")

    # orders
    sub.add_parser("orders", help="List all orders")

    # cancel
    p_cancel = sub.add_parser("cancel", help="Cancel an open order")
    p_cancel.add_argument("--id", type=int, required=True, help="Order ID to cancel")

    # check (fill open orders)
    p_check = sub.add_parser("check", help="Check open orders against live price")
    p_check.add_argument("--symbol", default="BTCUSDT")

    # reset
    sub.add_parser("reset", help="Reset paper account to $10,000")

    return parser


def main():
    print(BANNER)
    parser = build_parser()
    args = parser.parse_args()

    logger.info("Command: %s", args.command)

    dispatch = {
        "price": cmd_price,
        "order": cmd_order,
        "portfolio": cmd_portfolio,
        "orders": cmd_orders,
        "cancel": cmd_cancel,
        "check": cmd_check,
        "reset": cmd_reset,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
