"""
Analytics Router
Endpoints for retrieving trading analytics and performance metrics
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date
import logging
import traceback

from api.services.analytics_service import AnalyticsService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/equity-curve")
async def get_equity_curve(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get equity curve data (cumulative P&L over time)

    Returns daily cumulative realized P&L plus current unrealized P&L
    """
    try:
        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        service = AnalyticsService()
        data = service.get_equity_curve(start_date_obj, end_date_obj)

        return {'data': data}

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting equity curve: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get equity curve: {str(e)}")


@router.get("/performance-metrics")
async def get_performance_metrics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get comprehensive performance metrics

    Returns win rate, avg win/loss, profit factor, largest win/loss, etc.
    """
    try:
        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        service = AnalyticsService()
        metrics = service.get_performance_metrics(start_date_obj, end_date_obj)

        return {'metrics': metrics}

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/pnl-by-period")
async def get_pnl_by_period(
    period: str = Query('daily', description="Period: daily, weekly, or monthly"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get P&L aggregated by time period

    Returns realized P&L grouped by daily/weekly/monthly periods
    """
    try:
        # Validate period
        if period not in ['daily', 'weekly', 'monthly']:
            raise HTTPException(status_code=400, detail="Period must be one of: daily, weekly, monthly")

        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        service = AnalyticsService()
        data = service.get_pnl_by_period(period, start_date_obj, end_date_obj)

        return {'data': data}

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting P&L by period: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get P&L by period: {str(e)}")


@router.get("/pattern-performance")
async def get_pattern_performance(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get trade performance grouped by chart pattern

    Returns metrics for each pattern: count, win rate, avg P&L, total P&L
    """
    try:
        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        service = AnalyticsService()
        data = service.get_pattern_performance(start_date_obj, end_date_obj)

        return {'data': data}

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting pattern performance: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get pattern performance: {str(e)}")


@router.get("/position-breakdown")
async def get_position_breakdown():
    """
    Get current position P&L breakdown by symbol

    Returns unrealized P&L and position details for each active position
    """
    try:
        service = AnalyticsService()
        data = service.get_position_breakdown()

        return {'data': data}

    except Exception as e:
        logger.error(f"Error getting position breakdown: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get position breakdown: {str(e)}")


@router.get("/style-performance")
async def get_style_performance(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get trade performance grouped by trade style (SWING vs TREND)

    Returns metrics for each style: count, win rate, avg P&L, total P&L
    """
    try:
        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        service = AnalyticsService()
        data = service.get_style_performance(start_date_obj, end_date_obj)

        return {'data': data}

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting style performance: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get style performance: {str(e)}")


@router.get("/trade-distribution")
async def get_trade_distribution(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get trade P&L distribution for histogram

    Returns count of trades in each P&L bucket
    """
    try:
        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        service = AnalyticsService()
        data = service.get_trade_distribution(start_date_obj, end_date_obj)

        return {'data': data}

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting trade distribution: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get trade distribution: {str(e)}")


@router.get("/duration-analysis")
async def get_duration_analysis(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get trade duration analysis (days_open vs P&L)

    Returns scatter plot data for duration analysis
    """
    try:
        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        service = AnalyticsService()
        data = service.get_duration_analysis(start_date_obj, end_date_obj)

        return {'data': data}

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting duration analysis: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get duration analysis: {str(e)}")


@router.get("/drawdown-curve")
async def get_drawdown_curve(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get drawdown curve data

    Returns daily portfolio value with drawdown percentage
    """
    try:
        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        service = AnalyticsService()
        data = service.get_drawdown_curve(start_date_obj, end_date_obj)

        return {'data': data}

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting drawdown curve: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get drawdown curve: {str(e)}")
