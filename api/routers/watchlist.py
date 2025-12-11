"""
Watchlist Router
Endpoints for managing ticker watchlist with CRUD operations
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sys
import os
import logging
import traceback

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import TradingDB
from shared.models import (
    TickerWatchlist,
    CreateTickerWatchlist,
    UpdateTickerWatchlist,
    WatchlistListResponse,
    AlpacaAsset
)
from trading.alpaca_client import search_tickers

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=WatchlistListResponse)
async def get_watchlist(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by ticker or name"),
):
    """
    Get list of watchlist tickers with pagination and filters
    """
    db = TradingDB()

    try:
        # Build WHERE clause
        where_conditions = []
        params = []

        if exchange:
            where_conditions.append('"Exchange" = %s')
            params.append(exchange)

        if industry:
            where_conditions.append('"Industry" = %s')
            params.append(industry)

        if active is not None:
            where_conditions.append('"Active" = %s')
            params.append(active)

        if search:
            # Search in ticker field (case-insensitive)
            where_conditions.append('LOWER("Ticker") LIKE LOWER(%s)')
            params.append(f'%{search}%')

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        # Get total count
        count_query = 'SELECT COUNT(*) as count FROM ticker_watchlist'
        if where_clause:
            count_query += f' WHERE {where_clause}'

        count_result = db.execute_query(count_query, tuple(params) if params else None)
        total = count_result[0]['count'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * page_size
        results = db.query(
            'ticker_watchlist',
            where_clause=where_clause,
            params=tuple(params) if params else None,
            order_by='created_at DESC',
            limit=page_size,
            offset=offset
        )

        # Convert to Pydantic models
        tickers = [TickerWatchlist(**row) for row in results]

        return WatchlistListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=tickers
        )

    except Exception as e:
        logger.error(f"Error in watchlist endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{ticker_id}", response_model=TickerWatchlist)
async def get_watchlist_ticker(ticker_id: int):
    """
    Get a single watchlist ticker by ID
    """
    db = TradingDB()

    try:
        result = db.get_by_id('ticker_watchlist', ticker_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Ticker with ID {ticker_id} not found")

        return TickerWatchlist(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ticker {ticker_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/", response_model=TickerWatchlist)
async def create_watchlist_ticker(ticker_data: CreateTickerWatchlist):
    """
    Create a new watchlist ticker
    """
    db = TradingDB()

    try:
        # Check for duplicate ticker
        duplicate_check = db.query(
            'ticker_watchlist',
            where_clause='"Ticker" = %s',
            params=(ticker_data.Ticker,)
        )

        if duplicate_check:
            raise HTTPException(
                status_code=400,
                detail=f"Ticker {ticker_data.Ticker} already exists in watchlist"
            )

        # Insert new ticker
        ticker_id = db.insert(
            'ticker_watchlist',
            {
                'Ticker': ticker_data.Ticker,
                'Ticker_Name': ticker_data.Ticker_Name,
                'Exchange': ticker_data.Exchange,
                'Industry': ticker_data.Industry,
                'Active': ticker_data.Active
            }
        )

        # Fetch and return the created ticker
        result = db.get_by_id('ticker_watchlist', ticker_id)
        return TickerWatchlist(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ticker: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/{ticker_id}", response_model=TickerWatchlist)
async def update_watchlist_ticker(ticker_id: int, ticker_data: UpdateTickerWatchlist):
    """
    Update a watchlist ticker
    Note: Ticker symbol and Exchange cannot be updated (locked to Alpaca data)
    """
    db = TradingDB()

    try:
        # Check if ticker exists
        existing = db.get_by_id('ticker_watchlist', ticker_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Ticker with ID {ticker_id} not found")

        # Build update data (only updatable fields)
        update_data = {}
        if ticker_data.Industry is not None:
            update_data['Industry'] = ticker_data.Industry
        if ticker_data.Active is not None:
            update_data['Active'] = ticker_data.Active

        # Update the ticker
        db.update('ticker_watchlist', ticker_id, update_data)

        # Fetch and return the updated ticker
        result = db.get_by_id('ticker_watchlist', ticker_id)
        return TickerWatchlist(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticker {ticker_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/{ticker_id}")
async def delete_watchlist_ticker(ticker_id: int):
    """
    Delete a watchlist ticker
    """
    db = TradingDB()

    try:
        # Check if ticker exists
        existing = db.get_by_id('ticker_watchlist', ticker_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Ticker with ID {ticker_id} not found")

        # Delete the ticker
        delete_query = 'DELETE FROM ticker_watchlist WHERE id = %s'
        db.execute_update(delete_query, (ticker_id,))

        return {"message": f"Ticker {existing['Ticker']} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ticker {ticker_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/search-ticker/alpaca", response_model=List[AlpacaAsset])
async def search_alpaca_tickers(
    q: str = Query(..., description="Search query for ticker symbol or company name", min_length=1),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """
    Search Alpaca API for tradable tickers by symbol or company name
    """
    try:
        results = search_tickers(q, limit)
        return [AlpacaAsset(**asset) for asset in results]

    except Exception as e:
        logger.error(f"Error searching Alpaca tickers: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search tickers: {str(e)}"
        )


@router.get("/stats/summary")
async def get_watchlist_stats():
    """
    Get watchlist statistics (active count, total count)
    """
    db = TradingDB()

    try:
        # Get total count
        total_query = 'SELECT COUNT(*) as count FROM ticker_watchlist'
        total_result = db.execute_query(total_query)
        total = total_result[0]['count'] if total_result else 0

        # Get active count
        active_query = 'SELECT COUNT(*) as count FROM ticker_watchlist WHERE "Active" = true'
        active_result = db.execute_query(active_query)
        active = active_result[0]['count'] if active_result else 0

        return {
            'total': total,
            'active': active,
            'inactive': total - active
        }

    except Exception as e:
        logger.error(f"Error fetching watchlist stats: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
