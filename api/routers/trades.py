"""
Trade Journal Router
Endpoints for retrieving trade journal entries
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import TradingDB
from shared.models import TradeJournal, TradeListResponse

router = APIRouter()


@router.get("/", response_model=TradeListResponse)
async def get_trades(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by status (ORDERED, POSITION, CLOSED, CANCELLED)"),
    trade_style: Optional[str] = Query(None, description="Filter by trade style (SWING, TREND)"),
):
    """
    Get list of trade journal entries with pagination and filters
    """
    db = TradingDB()

    try:
        # Build WHERE clause
        where_conditions = []
        params = []

        if symbol:
            where_conditions.append('symbol = %s')
            params.append(symbol)

        if status:
            where_conditions.append('status = %s')
            params.append(status)

        if trade_style:
            where_conditions.append('trade_style = %s')
            params.append(trade_style)

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        # Get total count
        count_query = 'SELECT COUNT(*) as count FROM trade_journal'
        if where_clause:
            count_query += f' WHERE {where_clause}'

        count_result = db.execute_query(count_query, tuple(params) if params else None)
        total = count_result[0]['count'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * page_size
        results = db.query(
            'trade_journal',
            where_clause=where_clause,
            params=tuple(params) if params else None,
            order_by='created_at DESC',
            limit=page_size,
            offset=offset
        )

        # Convert to Pydantic models
        trades = [TradeJournal(**row) for row in results]

        return TradeListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=trades
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{trade_id}", response_model=TradeJournal)
async def get_trade(trade_id: int):
    """
    Get a single trade by ID
    """
    db = TradingDB()

    try:
        result = db.get_by_id('trade_journal', trade_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")

        return TradeJournal(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/active/list", response_model=TradeListResponse)
async def get_active_trades(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get active trades (status = POSITION)
    """
    db = TradingDB()

    try:
        where_clause = "status = 'POSITION'"

        # Get total count
        count_query = f'SELECT COUNT(*) as count FROM trade_journal WHERE {where_clause}'
        count_result = db.execute_query(count_query)
        total = count_result[0]['count'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * page_size
        results = db.query(
            'trade_journal',
            where_clause=where_clause,
            order_by='created_at DESC',
            limit=page_size,
            offset=offset
        )

        trades = [TradeJournal(**row) for row in results]

        return TradeListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=trades
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/stats/summary")
async def get_trade_stats():
    """
    Get summary statistics for trades
    """
    db = TradingDB()

    try:
        # Get status counts
        status_query = """
            SELECT status, COUNT(*) as count
            FROM trade_journal
            GROUP BY status
        """
        status_counts = db.execute_query(status_query)

        # Get P&L summary
        pnl_query = """
            SELECT
                COUNT(*) as total_closed,
                SUM(actual_pnl) as total_pnl,
                AVG(actual_pnl) as avg_pnl,
                MIN(actual_pnl) as min_pnl,
                MAX(actual_pnl) as max_pnl
            FROM trade_journal
            WHERE status = 'CLOSED' AND actual_pnl IS NOT NULL
        """
        pnl_stats = db.execute_query(pnl_query)

        return {
            "status_breakdown": {row['status']: row['count'] for row in status_counts},
            "pnl_summary": pnl_stats[0] if pnl_stats else {}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
