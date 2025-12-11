"""
Alpaca API Helper Module
Provides helper functions for Alpaca API interactions
"""
import os
import sys
import logging
import threading
from datetime import datetime
import time
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus
from alpaca.data.historical import StockHistoricalDataClient
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_PAPER

logger = logging.getLogger(__name__)

# Ticker cache for search optimization
_ticker_cache = {
    'data': None,           # List[dict] - pre-processed asset data
    'last_updated': None,   # datetime - last successful fetch
    'ttl_seconds': 3600     # 1 hour TTL
}
_ticker_cache_lock = threading.RLock()


def get_trading_client():
    """
    Initialize and return Alpaca TradingClient

    Returns:
        TradingClient: Configured Alpaca trading client

    Raises:
        ValueError: If API credentials are not configured
    """
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        raise ValueError(
            "Alpaca API credentials not configured. "
            "Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file"
        )

    try:
        client = TradingClient(
            api_key=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
            paper=ALPACA_PAPER
        )

        mode = "paper" if ALPACA_PAPER else "live"
        logger.info(f"Alpaca TradingClient initialized in {mode} mode")

        return client

    except Exception as e:
        logger.error(f"Failed to initialize Alpaca TradingClient: {e}")
        raise


def get_data_client():
    """
    Initialize and return Alpaca StockHistoricalDataClient

    Returns:
        StockHistoricalDataClient: Configured Alpaca data client

    Raises:
        ValueError: If API credentials are not configured
    """
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        raise ValueError(
            "Alpaca API credentials not configured. "
            "Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file"
        )

    try:
        client = StockHistoricalDataClient(
            api_key=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY
        )

        logger.info("Alpaca StockHistoricalDataClient initialized")

        return client

    except Exception as e:
        logger.error(f"Failed to initialize Alpaca StockHistoricalDataClient: {e}")
        raise


def handle_alpaca_error(error, operation):
    """
    Handle and log Alpaca API errors

    Args:
        error (Exception): The error that occurred
        operation (str): Description of the operation that failed

    Returns:
        str: Error message for logging/display
    """
    error_msg = f"Alpaca API error during {operation}: {str(error)}"
    logger.error(error_msg)

    # Check for specific error types
    if "rate limit" in str(error).lower():
        logger.warning("Rate limit exceeded. Consider adding retry logic with exponential backoff")
    elif "unauthorized" in str(error).lower():
        logger.error("Authentication failed. Check your API credentials")
    elif "insufficient" in str(error).lower():
        logger.warning("Insufficient buying power or position not found")

    return error_msg


def _refresh_ticker_cache():
    """
    Internal function to refresh ticker cache from Alpaca API
    Thread-safe cache update with error handling

    Returns:
        list: Cached ticker data

    Raises:
        Exception: If Alpaca API call fails
    """
    try:
        logger.info("Refreshing ticker cache from Alpaca API...")
        start_time = time.time()

        client = get_trading_client()
        request = GetAssetsRequest(
            asset_class=AssetClass.US_EQUITY,
            status=AssetStatus.ACTIVE
        )
        assets = client.get_all_assets(filter=request)

        # Pre-process to cache format
        cache_data = []
        for asset in assets:
            cache_data.append({
                'symbol': asset.symbol,
                'name': asset.name,
                'exchange': asset.exchange.value if hasattr(asset.exchange, 'value') else str(asset.exchange),
                'asset_class': asset.asset_class.value if hasattr(asset.asset_class, 'value') else str(asset.asset_class),
                'tradable': asset.tradable
            })

        # Atomic update
        with _ticker_cache_lock:
            _ticker_cache['data'] = cache_data
            _ticker_cache['last_updated'] = datetime.now()

        duration = time.time() - start_time
        logger.info(f"Ticker cache refreshed: {len(cache_data)} assets in {duration:.2f}s")

        return cache_data

    except Exception as e:
        logger.error(f"Failed to refresh ticker cache: {str(e)}")
        raise


def search_tickers(query: str, limit: int = 10):
    """
    Search Alpaca tradable assets by symbol or name (with caching)

    Uses in-memory cache with 1-hour TTL to reduce response time from 4s to <50ms.
    Thread-safe implementation for concurrent requests.

    Args:
        query (str): Search query (symbol or company name)
        limit (int): Maximum number of results to return (default: 10)

    Returns:
        list: List of matching assets with symbol, name, exchange, asset_class, tradable

    Raises:
        Exception: If Alpaca API call fails and no cache available
    """
    start_time = time.time()
    cache_hit = False

    try:
        with _ticker_cache_lock:
            # Check if cache needs refresh
            needs_refresh = (
                _ticker_cache['data'] is None or
                _ticker_cache['last_updated'] is None or
                (datetime.now() - _ticker_cache['last_updated']).total_seconds() > _ticker_cache['ttl_seconds']
            )

            if needs_refresh:
                try:
                    cache_data = _refresh_ticker_cache()
                except Exception as e:
                    # Fallback to stale cache if available
                    if _ticker_cache['data'] is not None:
                        cache_age = (datetime.now() - _ticker_cache['last_updated']).total_seconds()
                        logger.warning(f"Using stale ticker cache (age: {cache_age/3600:.1f}h) due to refresh error: {e}")
                        cache_data = _ticker_cache['data']
                    else:
                        # No cache available, must fail
                        error_msg = handle_alpaca_error(e, f"ticker cache refresh")
                        raise Exception(error_msg)
            else:
                # Cache is fresh
                cache_hit = True
                cache_data = _ticker_cache['data']

        # Search in cache (no lock needed - data is immutable)
        query_upper = query.upper()
        query_lower = query.lower()

        matches = []
        for asset in cache_data:
            if query_upper in asset['symbol'] or query_lower in asset['name'].lower():
                matches.append(asset)
                if len(matches) >= limit:
                    break

        # Log performance
        duration = time.time() - start_time
        if cache_hit:
            logger.info(f"Ticker cache HIT for '{query}': {len(matches)} results in {duration*1000:.1f}ms")
        else:
            logger.info(f"Ticker cache MISS for '{query}': refreshed and found {len(matches)} results in {duration:.2f}s")

        return matches

    except Exception as e:
        error_msg = handle_alpaca_error(e, f"ticker search for '{query}'")
        raise Exception(error_msg)
