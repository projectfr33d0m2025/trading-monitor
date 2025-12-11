"""
Alpaca API Helper Module
Provides helper functions for Alpaca API interactions
"""
import os
import sys
import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus
from alpaca.data.historical import StockHistoricalDataClient
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_PAPER

logger = logging.getLogger(__name__)


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


def search_tickers(query: str, limit: int = 10):
    """
    Search Alpaca tradable assets by symbol or name

    Args:
        query (str): Search query (symbol or company name)
        limit (int): Maximum number of results to return (default: 10)

    Returns:
        list: List of matching assets with symbol, name, exchange, asset_class, tradable

    Raises:
        Exception: If Alpaca API call fails
    """
    try:
        client = get_trading_client()

        # Create request to get all active US equity assets
        request = GetAssetsRequest(
            asset_class=AssetClass.US_EQUITY,
            status=AssetStatus.ACTIVE
        )

        assets = client.get_all_assets(filter=request)

        # Filter by query (symbol or name contains query, case-insensitive)
        query_upper = query.upper()
        query_lower = query.lower()

        matches = []
        for asset in assets:
            # Check if query matches symbol or name
            if query_upper in asset.symbol or query_lower in asset.name.lower():
                matches.append({
                    'symbol': asset.symbol,
                    'name': asset.name,
                    'exchange': asset.exchange.value if hasattr(asset.exchange, 'value') else str(asset.exchange),
                    'asset_class': asset.asset_class.value if hasattr(asset.asset_class, 'value') else str(asset.asset_class),
                    'tradable': asset.tradable
                })

                # Stop if we reached the limit
                if len(matches) >= limit:
                    break

        logger.info(f"Found {len(matches)} assets matching '{query}'")
        return matches

    except Exception as e:
        error_msg = handle_alpaca_error(e, f"ticker search for '{query}'")
        raise Exception(error_msg)
