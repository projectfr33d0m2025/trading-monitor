"""
Analysis Decision Router
Endpoints for retrieving analysis decisions from n8n workflow
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
from shared.models import AnalysisDecision, AnalysisListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=AnalysisListResponse)
async def get_analyses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    executed: Optional[bool] = Query(None, description="Filter by execution status"),
    approved: Optional[bool] = Query(None, description="Filter by approval status"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD format)"),
):
    """
    Get list of analysis decisions with pagination and filters
    """
    db = TradingDB()

    try:
        # Build WHERE clause
        where_conditions = []
        params = []

        if ticker:
            where_conditions.append('"Ticker" = %s')
            params.append(ticker)

        if executed is not None:
            where_conditions.append('executed = %s')
            params.append(executed)

        if approved is not None:
            where_conditions.append('"Approve" = %s')
            params.append(approved)

        if date:
            # Filter by date - cast Date_time to date for comparison
            where_conditions.append('DATE("Date_time") = %s')
            params.append(date)

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        # Get total count
        count_query = 'SELECT COUNT(*) as count FROM analysis_decision'
        if where_clause:
            count_query += f' WHERE {where_clause}'

        count_result = db.execute_query(count_query, tuple(params) if params else None)
        total = count_result[0]['count'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * page_size
        results = db.query(
            'analysis_decision',
            where_clause=where_clause,
            params=tuple(params) if params else None,
            order_by='"Date_time" DESC',
            limit=page_size,
            offset=offset
        )

        # Convert to Pydantic models
        analyses = [AnalysisDecision(**row) for row in results]

        return AnalysisListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=analyses
        )

    except Exception as e:
        logger.error(f"Error in analysis endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{analysis_id}", response_model=AnalysisDecision)
async def get_analysis(analysis_id: str):
    """
    Get a single analysis decision by ID
    """
    db = TradingDB()

    try:
        results = db.query(
            'analysis_decision',
            where_clause='"Analysis_Id" = %s',
            params=(analysis_id,)
        )

        if not results:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

        return AnalysisDecision(**results[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/pending-approvals/list", response_model=AnalysisListResponse)
async def get_pending_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get analyses pending approval (not approved and not executed)
    """
    db = TradingDB()

    try:
        where_clause = '"Approve" = false AND executed = false'

        # Get total count
        count_query = f'SELECT COUNT(*) as count FROM analysis_decision WHERE {where_clause}'
        count_result = db.execute_query(count_query)
        total = count_result[0]['count'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * page_size
        results = db.query(
            'analysis_decision',
            where_clause=where_clause,
            order_by='"Date_time" DESC',
            limit=page_size,
            offset=offset
        )

        analyses = [AnalysisDecision(**row) for row in results]

        return AnalysisListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=analyses
        )

    except Exception as e:
        logger.error(f"Error in analysis endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/stats/summary")
async def get_analysis_stats():
    """
    Get analysis statistics including counts by status
    """
    db = TradingDB()

    try:
        # Get total analyses
        total_query = "SELECT COUNT(*) as count FROM analysis_decision"
        total_result = db.execute_query(total_query)
        total_analyses = total_result[0]['count'] if total_result else 0

        # Get pending count (not approved and not executed)
        pending_query = 'SELECT COUNT(*) as count FROM analysis_decision WHERE "Approve" = false AND executed = false'
        pending_result = db.execute_query(pending_query)
        pending_count = pending_result[0]['count'] if pending_result else 0

        # Get approved count (approved but not executed)
        approved_query = 'SELECT COUNT(*) as count FROM analysis_decision WHERE "Approve" = true AND executed = false'
        approved_result = db.execute_query(approved_query)
        approved_count = approved_result[0]['count'] if approved_result else 0

        # Get executed count
        executed_query = 'SELECT COUNT(*) as count FROM analysis_decision WHERE executed = true'
        executed_result = db.execute_query(executed_query)
        executed_count = executed_result[0]['count'] if executed_result else 0

        # Get breakdown by trade type
        type_query = """
            SELECT
                "Trade_Type",
                COUNT(*) as count
            FROM analysis_decision
            WHERE "Trade_Type" IS NOT NULL
            GROUP BY "Trade_Type"
        """
        type_results = db.execute_query(type_query)
        type_breakdown = {row['Trade_Type']: row['count'] for row in type_results}

        return {
            'total_analyses': total_analyses,
            'status_breakdown': {
                'PENDING': pending_count,
                'APPROVED': approved_count,
                'EXECUTED': executed_count
            },
            'type_breakdown': type_breakdown
        }

    except Exception as e:
        logger.error(f"Error in analysis endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
