"""
Position Tracking Router
Endpoints for retrieving current positions and P&L data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import TradingDB
from shared.models import PositionTracking, PositionListResponse

router = APIRouter()


@router.get("/", response_model=PositionListResponse)
async def get_positions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
):
    """
    Get list of current positions with pagination and filters
    """
    db = TradingDB()

    try:
        # Build WHERE clause
        where_conditions = []
        params = []

        if symbol:
            where_conditions.append('symbol = %s')
            params.append(symbol)

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        # Get total count
        count_query = 'SELECT COUNT(*) as count FROM position_tracking'
        if where_clause:
            count_query += f' WHERE {where_clause}'

        count_result = db.execute_query(count_query, tuple(params) if params else None)
        total = count_result[0]['count'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * page_size
        results = db.query(
            'position_tracking',
            where_clause=where_clause,
            params=tuple(params) if params else None,
            order_by='last_updated DESC',
            limit=page_size,
            offset=offset
        )

        # Convert to Pydantic models
        positions = [PositionTracking(**row) for row in results]

        return PositionListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=positions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{position_id}", response_model=PositionTracking)
async def get_position(position_id: int):
    """
    Get a single position by ID
    """
    db = TradingDB()

    try:
        result = db.get_by_id('position_tracking', position_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

        return PositionTracking(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/pnl/summary")
async def get_pnl_summary():
    """
    Get P&L summary for all current positions
    """
    db = TradingDB()

    try:
        pnl_query = """
            SELECT
                COUNT(*) as total_positions,
                SUM(unrealized_pnl) as total_unrealized_pnl,
                SUM(market_value) as total_market_value,
                SUM(cost_basis) as total_cost_basis,
                AVG(unrealized_pnl) as avg_unrealized_pnl
            FROM position_tracking
        """
        pnl_stats = db.execute_query(pnl_query)

        # Get breakdown by symbol
        symbol_query = """
            SELECT
                symbol,
                qty,
                avg_entry_price,
                current_price,
                market_value,
                unrealized_pnl
            FROM position_tracking
            ORDER BY unrealized_pnl DESC
        """
        symbol_breakdown = db.execute_query(symbol_query)

        return {
            "summary": pnl_stats[0] if pnl_stats else {},
            "by_symbol": symbol_breakdown
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
