from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(ValueError):
    pass


def validate_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not symbol or not symbol.isalnum():
        raise ValidationError(f"Invalid symbol: '{symbol}'. Example: BTCUSDT")
    return symbol


def validate_side(side: str) -> str:
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Side must be BUY or SELL. Got: '{side}'")
    return side


def validate_order_type(order_type: str) -> str:
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(f"Order type must be one of {VALID_ORDER_TYPES}. Got: '{order_type}'")
    return order_type


def validate_quantity(quantity) -> float:
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a positive number. Got: '{quantity}'")
    if qty <= 0:
        raise ValidationError(f"Quantity must be > 0. Got: {qty}")
    return qty


def validate_price(price, order_type: str):
    if order_type == "MARKET":
        return None
    if price is None:
        raise ValidationError(f"Price is required for {order_type} orders.")
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"Price must be a positive number. Got: '{price}'")
    if p <= 0:
        raise ValidationError(f"Price must be > 0. Got: {p}")
    return p


def validate_stop_price(stop_price, order_type: str):
    if order_type != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValidationError("Stop price is required for STOP_MARKET orders.")
    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValidationError(f"Stop price must be a positive number. Got: '{stop_price}'")
    if sp <= 0:
        raise ValidationError(f"Stop price must be > 0. Got: {sp}")
    return sp


def validate_all(symbol, side, order_type, quantity, price=None, stop_price=None) -> dict:
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.strip().upper()),
        "stop_price": validate_stop_price(stop_price, order_type.strip().upper()),
    }
