"""
Alpaca API Helper Module
Provides helper functions for Alpaca API interactions
"""
import os
import sys
import logging
from alpaca.trading.client import TradingClient
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
