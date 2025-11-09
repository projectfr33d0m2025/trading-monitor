"""
Analysis Decision Router
Endpoints for retrieving analysis decisions from n8n workflow
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import TradingDB
from shared.models import AnalysisDecision, AnalysisListResponse

router = APIRouter()


@router.get("/", response_model=AnalysisListResponse)
async def get_analyses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    executed: Optional[bool] = Query(None, description="Filter by execution status"),
    approved: Optional[bool] = Query(None, description="Filter by approval status"),
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
