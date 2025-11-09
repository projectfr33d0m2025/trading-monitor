"""
Order Execution Router
Endpoints for retrieving order execution records
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
from shared.models import OrderExecution, OrderListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=OrderListResponse)
async def get_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    trade_journal_id: Optional[int] = Query(None, description="Filter by trade journal ID"),
    order_type: Optional[str] = Query(None, description="Filter by order type (ENTRY, STOP_LOSS, TAKE_PROFIT)"),
    order_status: Optional[str] = Query(None, description="Filter by order status"),
    side: Optional[str] = Query(None, description="Filter by side (buy/sell)"),
):
    """
    Get list of order executions with pagination and filters
    """
    db = TradingDB()

    try:
        # Build WHERE clause
        where_conditions = []
        params = []

        if trade_journal_id:
            where_conditions.append('trade_journal_id = %s')
            params.append(trade_journal_id)

        if order_type:
            where_conditions.append('order_type = %s')
            params.append(order_type)

        if order_status:
            where_conditions.append('order_status = %s')
            params.append(order_status)

        if side:
            where_conditions.append('side = %s')
            params.append(side)

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        # Get total count
        count_query = 'SELECT COUNT(*) as count FROM order_execution'
        if where_clause:
            count_query += f' WHERE {where_clause}'

        count_result = db.execute_query(count_query, tuple(params) if params else None)
        total = count_result[0]['count'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * page_size
        results = db.query(
            'order_execution',
            where_clause=where_clause,
            params=tuple(params) if params else None,
            order_by='created_at DESC',
            limit=page_size,
            offset=offset
        )

        # Convert to Pydantic models
        orders = [OrderExecution(**row) for row in results]

        return OrderListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=orders
        )

    except Exception as e:
        logger.error(f"Error in orders endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{order_id}", response_model=OrderExecution)
async def get_order(order_id: int):
    """
    Get a single order by ID
    """
    db = TradingDB()

    try:
        result = db.get_by_id('order_execution', order_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        return OrderExecution(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/trade/{trade_id}/list", response_model=OrderListResponse)
async def get_orders_by_trade(
    trade_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get all orders for a specific trade
    """
    db = TradingDB()

    try:
        where_clause = "trade_journal_id = %s"

        # Get total count
        count_query = f'SELECT COUNT(*) as count FROM order_execution WHERE {where_clause}'
        count_result = db.execute_query(count_query, (trade_id,))
        total = count_result[0]['count'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * page_size
        results = db.query(
            'order_execution',
            where_clause=where_clause,
            params=(trade_id,),
            order_by='created_at DESC',
            limit=page_size,
            offset=offset
        )

        orders = [OrderExecution(**row) for row in results]

        return OrderListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=orders
        )

    except Exception as e:
        logger.error(f"Error in orders endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/stats/summary")
async def get_order_stats():
    """
    Get order statistics including counts by type and status
    """
    db = TradingDB()

    try:
        # Get total orders
        total_query = "SELECT COUNT(*) as count FROM order_execution"
        total_result = db.execute_query(total_query)
        total_orders = total_result[0]['count'] if total_result else 0

        # Get breakdown by order type
        type_query = """
            SELECT
                order_type,
                COUNT(*) as count
            FROM order_execution
            GROUP BY order_type
        """
        type_results = db.execute_query(type_query)
        type_breakdown = {row['order_type']: row['count'] for row in type_results}

        # Get breakdown by order status
        status_query = """
            SELECT
                order_status,
                COUNT(*) as count
            FROM order_execution
            GROUP BY order_status
        """
        status_results = db.execute_query(status_query)
        status_breakdown = {row['order_status']: row['count'] for row in status_results}

        return {
            'total_orders': total_orders,
            'type_breakdown': type_breakdown,
            'status_breakdown': status_breakdown
        }

    except Exception as e:
        logger.error(f"Error in orders endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
