"""
market.py — Fetches live market data from Binance public REST API.
No API key required. Uses /api/v3 endpoints (spot) which are publicly accessible.
"""
from __future__ import annotations

import requests
from bot.logging_config import setup_logger

BASE_URL = "https://api.binance.com"
logger = setup_logger("market")


class MarketDataError(Exception):
    pass


def get_ticker_price(symbol: str) -> float:
    """Fetch the latest price for a symbol from Binance public API."""
    url = f"{BASE_URL}/api/v3/ticker/price"
    params = {"symbol": symbol.upper()}
    logger.debug("Fetching price for %s", symbol)
    try:
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if "code" in data:
            raise MarketDataError(f"Binance error {data['code']}: {data.get('msg')}")
        price = float(data["price"])
        logger.info("Live price for %s: $%.2f", symbol, price)
        return price
    except requests.RequestException as e:
        logger.error("Network error fetching price: %s", e)
        raise


def get_24hr_ticker(symbol: str) -> dict:
    """Fetch 24hr statistics for a symbol."""
    url = f"{BASE_URL}/api/v3/ticker/24hr"
    params = {"symbol": symbol.upper()}
    logger.debug("Fetching 24hr stats for %s", symbol)
    try:
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if "code" in data:
            raise MarketDataError(f"Binance error {data['code']}: {data.get('msg')}")
        logger.info(
            "%s | Last: $%s | Change: %s%% | High: $%s | Low: $%s",
            symbol, data["lastPrice"], data["priceChangePercent"],
            data["highPrice"], data["lowPrice"]
        )
        return data
    except requests.RequestException as e:
        logger.error("Network error fetching 24hr stats: %s", e)
        raise


def get_order_book(symbol: str, limit: int = 5) -> dict:
    """Fetch top N bids and asks."""
    url = f"{BASE_URL}/api/v3/depth"
    params = {"symbol": symbol.upper(), "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if "code" in data:
            raise MarketDataError(f"Binance error {data['code']}: {data.get('msg')}")
        return data
    except requests.RequestException as e:
        logger.error("Network error fetching order book: %s", e)
        raise
