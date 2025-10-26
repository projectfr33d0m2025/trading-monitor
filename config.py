"""
Configuration Module
Loads environment variables and provides configuration based on mode (production vs test).
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_postgres_config(test_mode=False):
    """
    Get PostgreSQL configuration based on mode

    Args:
        test_mode (bool): If True, use TEST_ prefixed environment variables

    Returns:
        dict: PostgreSQL connection configuration
    """
    prefix = 'TEST_' if test_mode else ''

    return {
        'host': os.getenv(f'{prefix}POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv(f'{prefix}POSTGRES_PORT', '5432')),
        'database': os.getenv(f'{prefix}POSTGRES_DB', 'nocodb' if not test_mode else 'test'),
        'user': os.getenv(f'{prefix}POSTGRES_USER', 'postgres'),
        'password': os.getenv(f'{prefix}POSTGRES_PASSWORD', '')
    }


# Alpaca API Configuration
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
ALPACA_PAPER = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'

# Trading Schedule Configuration (US Eastern Time)
TRADING_START_HOUR = int(os.getenv('TRADING_START_HOUR', '9'))
TRADING_START_MINUTE = int(os.getenv('TRADING_START_MINUTE', '30'))
TRADING_END_HOUR = int(os.getenv('TRADING_END_HOUR', '16'))
TRADING_END_MINUTE = int(os.getenv('TRADING_END_MINUTE', '0'))
