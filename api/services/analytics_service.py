"""
Analytics Service Layer
Business logic for calculating trading performance metrics and analytics data
"""
import sys
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import TradingDB

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service class for analytics calculations"""

    def __init__(self):
        self.db = TradingDB()

    def get_equity_curve(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate cumulative P&L over time (equity curve)

        Returns daily cumulative realized P&L plus current unrealized P&L
        """
        # Build WHERE clause for date filtering
        where_conditions = ["status = 'CLOSED'", "exit_date IS NOT NULL"]
        params = []

        if start_date:
            where_conditions.append("exit_date >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("exit_date <= %s")
            params.append(end_date)

        where_clause = " AND ".join(where_conditions)

        # Query for daily realized P&L from closed trades
        query = f"""
            WITH daily_pnl AS (
                SELECT
                    DATE(exit_date) as date,
                    SUM(actual_pnl) as daily_realized_pnl
                FROM trade_journal
                WHERE {where_clause}
                GROUP BY DATE(exit_date)
                ORDER BY DATE(exit_date)
            ),
            cumulative AS (
                SELECT
                    date,
                    daily_realized_pnl,
                    SUM(daily_realized_pnl) OVER (ORDER BY date) as cumulative_realized_pnl
                FROM daily_pnl
            )
            SELECT
                date,
                daily_realized_pnl as realized_pnl,
                cumulative_realized_pnl as cumulative_pnl
            FROM cumulative
            ORDER BY date
        """

        results = self.db.execute_query(query, tuple(params) if params else None)

        # Get current total unrealized P&L from active positions
        unrealized_query = """
            SELECT COALESCE(SUM(unrealized_pnl), 0) as total_unrealized_pnl
            FROM position_tracking
        """
        unrealized_result = self.db.execute_query(unrealized_query)
        total_unrealized_pnl = float(unrealized_result[0]['total_unrealized_pnl']) if unrealized_result else 0.0

        # Convert to list of dicts and add unrealized P&L to cumulative
        equity_curve = []
        for row in results:
            equity_curve.append({
                'date': row['date'].isoformat() if isinstance(row['date'], date) else row['date'],
                'realized_pnl': float(row['realized_pnl']) if row['realized_pnl'] else 0.0,
                'cumulative_pnl': float(row['cumulative_pnl']) + total_unrealized_pnl if row['cumulative_pnl'] else total_unrealized_pnl,
                'unrealized_pnl': total_unrealized_pnl
            })

        return equity_curve

    def get_performance_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics

        Returns win rate, avg win/loss, profit factor, largest win/loss, etc.
        """
        # Build WHERE clause for date filtering
        where_conditions = ["status = 'CLOSED'", "actual_pnl IS NOT NULL"]
        params = []

        if start_date:
            where_conditions.append("exit_date >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("exit_date <= %s")
            params.append(end_date)

        where_clause = " AND ".join(where_conditions)

        # Query for performance metrics
        query = f"""
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN actual_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN actual_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(CASE WHEN actual_pnl = 0 THEN 1 ELSE 0 END) as breakeven_trades,
                COALESCE(
                    ROUND(100.0 * SUM(CASE WHEN actual_pnl > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2),
                    0
                ) as win_rate,
                COALESCE(AVG(CASE WHEN actual_pnl > 0 THEN actual_pnl END), 0) as avg_win,
                COALESCE(AVG(CASE WHEN actual_pnl < 0 THEN actual_pnl END), 0) as avg_loss,
                COALESCE(MAX(actual_pnl), 0) as largest_win,
                COALESCE(MIN(actual_pnl), 0) as largest_loss,
                COALESCE(SUM(CASE WHEN actual_pnl > 0 THEN actual_pnl ELSE 0 END), 0) as total_wins,
                COALESCE(ABS(SUM(CASE WHEN actual_pnl < 0 THEN actual_pnl ELSE 0 END)), 0) as total_losses,
                COALESCE(SUM(actual_pnl), 0) as total_pnl
            FROM trade_journal
            WHERE {where_clause}
        """

        result = self.db.execute_query(query, tuple(params) if params else None)

        if not result or result[0]['total_trades'] == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'total_wins': 0.0,
                'total_losses': 0.0,
                'total_pnl': 0.0
            }

        metrics = result[0]

        # Calculate profit factor
        total_losses = float(metrics['total_losses']) if metrics['total_losses'] else 0.0
        profit_factor = float(metrics['total_wins']) / total_losses if total_losses > 0 else 0.0

        return {
            'total_trades': int(metrics['total_trades']),
            'winning_trades': int(metrics['winning_trades']),
            'losing_trades': int(metrics['losing_trades']),
            'win_rate': float(metrics['win_rate']),
            'avg_win': float(metrics['avg_win']) if metrics['avg_win'] else 0.0,
            'avg_loss': float(metrics['avg_loss']) if metrics['avg_loss'] else 0.0,
            'profit_factor': round(profit_factor, 2),
            'largest_win': float(metrics['largest_win']) if metrics['largest_win'] else 0.0,
            'largest_loss': float(metrics['largest_loss']) if metrics['largest_loss'] else 0.0,
            'total_wins': float(metrics['total_wins']) if metrics['total_wins'] else 0.0,
            'total_losses': float(metrics['total_losses']) if metrics['total_losses'] else 0.0,
            'total_pnl': float(metrics['total_pnl']) if metrics['total_pnl'] else 0.0
        }

    def get_pnl_by_period(
        self,
        period: str = 'daily',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate P&L by time period (daily, weekly, monthly)

        Args:
            period: One of 'daily', 'weekly', 'monthly'
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of dicts with period, realized_pnl, unrealized_pnl, total_pnl
        """
        # Map period to SQL date truncation
        period_map = {
            'daily': 'DATE(exit_date)',
            'weekly': "DATE_TRUNC('week', exit_date)::date",
            'monthly': "DATE_TRUNC('month', exit_date)::date"
        }

        if period not in period_map:
            raise ValueError(f"Invalid period: {period}. Must be one of: daily, weekly, monthly")

        period_expr = period_map[period]

        # Build WHERE clause for date filtering
        where_conditions = ["status = 'CLOSED'", "exit_date IS NOT NULL", "actual_pnl IS NOT NULL"]
        params = []

        if start_date:
            where_conditions.append("exit_date >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("exit_date <= %s")
            params.append(end_date)

        where_clause = " AND ".join(where_conditions)

        # Query for P&L by period
        query = f"""
            SELECT
                {period_expr} as period,
                SUM(actual_pnl) as realized_pnl,
                0 as unrealized_pnl,
                SUM(actual_pnl) as total_pnl
            FROM trade_journal
            WHERE {where_clause}
            GROUP BY {period_expr}
            ORDER BY {period_expr}
        """

        results = self.db.execute_query(query, tuple(params) if params else None)

        # Convert to list of dicts
        pnl_by_period = []
        for row in results:
            pnl_by_period.append({
                'period': row['period'].isoformat() if isinstance(row['period'], date) else row['period'],
                'realized_pnl': float(row['realized_pnl']) if row['realized_pnl'] else 0.0,
                'unrealized_pnl': 0.0,  # Only realized P&L in historical periods
                'total_pnl': float(row['total_pnl']) if row['total_pnl'] else 0.0
            })

        return pnl_by_period

    def get_pattern_performance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trade performance grouped by chart pattern

        Returns metrics for each pattern: count, win rate, avg P&L, total P&L
        """
        # Build WHERE clause for date filtering
        where_conditions = ["status = 'CLOSED'", "actual_pnl IS NOT NULL", "pattern IS NOT NULL"]
        params = []

        if start_date:
            where_conditions.append("exit_date >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("exit_date <= %s")
            params.append(end_date)

        where_clause = " AND ".join(where_conditions)

        # Query for pattern performance
        query = f"""
            SELECT
                pattern,
                COUNT(*) as trade_count,
                SUM(CASE WHEN actual_pnl > 0 THEN 1 ELSE 0 END) as wins,
                COALESCE(
                    ROUND(100.0 * SUM(CASE WHEN actual_pnl > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2),
                    0
                ) as win_rate,
                COALESCE(AVG(actual_pnl), 0) as avg_pnl,
                COALESCE(SUM(actual_pnl), 0) as total_pnl
            FROM trade_journal
            WHERE {where_clause}
            GROUP BY pattern
            ORDER BY total_pnl DESC
        """

        results = self.db.execute_query(query, tuple(params) if params else None)

        # Convert to list of dicts
        pattern_performance = []
        for row in results:
            pattern_performance.append({
                'pattern': row['pattern'],
                'trade_count': int(row['trade_count']),
                'wins': int(row['wins']),
                'win_rate': float(row['win_rate']),
                'avg_pnl': float(row['avg_pnl']) if row['avg_pnl'] else 0.0,
                'total_pnl': float(row['total_pnl']) if row['total_pnl'] else 0.0
            })

        return pattern_performance

    def get_position_breakdown(self) -> List[Dict[str, Any]]:
        """
        Get current position P&L breakdown by symbol

        Returns unrealized P&L and position details for each active position
        """
        query = """
            SELECT
                symbol,
                qty,
                avg_entry_price,
                current_price,
                market_value,
                cost_basis,
                unrealized_pnl,
                CASE
                    WHEN cost_basis > 0 THEN ROUND(100.0 * unrealized_pnl / cost_basis, 2)
                    ELSE 0
                END as unrealized_pnl_pct
            FROM position_tracking
            ORDER BY ABS(unrealized_pnl) DESC
        """

        results = self.db.execute_query(query)

        # Convert to list of dicts
        position_breakdown = []
        for row in results:
            position_breakdown.append({
                'symbol': row['symbol'],
                'qty': int(row['qty']),
                'avg_entry_price': float(row['avg_entry_price']) if row['avg_entry_price'] else 0.0,
                'current_price': float(row['current_price']) if row['current_price'] else 0.0,
                'market_value': float(row['market_value']) if row['market_value'] else 0.0,
                'cost_basis': float(row['cost_basis']) if row['cost_basis'] else 0.0,
                'unrealized_pnl': float(row['unrealized_pnl']) if row['unrealized_pnl'] else 0.0,
                'unrealized_pnl_pct': float(row['unrealized_pnl_pct']) if row['unrealized_pnl_pct'] else 0.0
            })

        return position_breakdown

    def get_style_performance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trade performance grouped by trade style (SWING vs TREND)

        Returns metrics for each style: count, win rate, avg P&L, total P&L
        """
        # Build WHERE clause for date filtering
        where_conditions = ["status = 'CLOSED'", "actual_pnl IS NOT NULL", "trade_style IS NOT NULL"]
        params = []

        if start_date:
            where_conditions.append("exit_date >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("exit_date <= %s")
            params.append(end_date)

        where_clause = " AND ".join(where_conditions)

        # Query for style performance
        query = f"""
            SELECT
                trade_style,
                COUNT(*) as trade_count,
                COALESCE(
                    ROUND(100.0 * SUM(CASE WHEN actual_pnl > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2),
                    0
                ) as win_rate,
                COALESCE(AVG(actual_pnl), 0) as avg_pnl,
                COALESCE(SUM(actual_pnl), 0) as total_pnl
            FROM trade_journal
            WHERE {where_clause}
            GROUP BY trade_style
            ORDER BY total_pnl DESC
        """

        results = self.db.execute_query(query, tuple(params) if params else None)

        # Convert to list of dicts
        style_performance = []
        for row in results:
            style_performance.append({
                'trade_style': row['trade_style'],
                'trade_count': int(row['trade_count']),
                'win_rate': float(row['win_rate']),
                'avg_pnl': float(row['avg_pnl']) if row['avg_pnl'] else 0.0,
                'total_pnl': float(row['total_pnl']) if row['total_pnl'] else 0.0
            })

        return style_performance

    def get_trade_distribution(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trade P&L distribution for histogram

        Returns count of trades in each P&L bucket
        """
        # Build WHERE clause for date filtering
        where_conditions = ["status = 'CLOSED'", "actual_pnl IS NOT NULL"]
        params = []

        if start_date:
            where_conditions.append("exit_date >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("exit_date <= %s")
            params.append(end_date)

        where_clause = " AND ".join(where_conditions)

        # Define P&L buckets
        buckets = [
            {'label': 'Heavy Loss (< -$100)', 'min': None, 'max': -100},
            {'label': 'Loss (-$100 to -$50)', 'min': -100, 'max': -50},
            {'label': 'Small Loss (-$50 to $0)', 'min': -50, 'max': 0},
            {'label': 'Small Win ($0 to $50)', 'min': 0, 'max': 50},
            {'label': 'Win ($50 to $100)', 'min': 50, 'max': 100},
            {'label': 'Large Win (> $100)', 'min': 100, 'max': None}
        ]

        distribution = []

        for bucket in buckets:
            # Build bucket-specific WHERE clause
            bucket_conditions = where_conditions.copy()
            bucket_params = params.copy()

            if bucket['min'] is not None:
                bucket_conditions.append("actual_pnl >= %s")
                bucket_params.append(bucket['min'])

            if bucket['max'] is not None:
                bucket_conditions.append("actual_pnl < %s")
                bucket_params.append(bucket['max'])

            bucket_where_clause = " AND ".join(bucket_conditions)

            # Query for count in this bucket
            query = f"""
                SELECT COUNT(*) as trade_count
                FROM trade_journal
                WHERE {bucket_where_clause}
            """

            result = self.db.execute_query(query, tuple(bucket_params) if bucket_params else None)
            count = int(result[0]['trade_count']) if result else 0

            distribution.append({
                'bucket_label': bucket['label'],
                'min_pnl': bucket['min'],
                'max_pnl': bucket['max'],
                'trade_count': count
            })

        return distribution

    def get_duration_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trade duration analysis (days_open vs P&L)

        Returns scatter plot data for duration analysis
        """
        # Build WHERE clause for date filtering
        where_conditions = ["status = 'CLOSED'", "actual_pnl IS NOT NULL", "days_open IS NOT NULL"]
        params = []

        if start_date:
            where_conditions.append("exit_date >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("exit_date <= %s")
            params.append(end_date)

        where_clause = " AND ".join(where_conditions)

        # Query for duration analysis
        query = f"""
            SELECT
                trade_id,
                symbol,
                days_open,
                actual_pnl,
                CASE WHEN actual_pnl > 0 THEN true ELSE false END as is_winner
            FROM trade_journal
            WHERE {where_clause}
            ORDER BY days_open
        """

        results = self.db.execute_query(query, tuple(params) if params else None)

        # Convert to list of dicts
        duration_analysis = []
        for row in results:
            duration_analysis.append({
                'trade_id': row['trade_id'],
                'symbol': row['symbol'],
                'days_open': int(row['days_open']) if row['days_open'] else 0,
                'actual_pnl': float(row['actual_pnl']) if row['actual_pnl'] else 0.0,
                'is_winner': bool(row['is_winner'])
            })

        return duration_analysis

    def get_drawdown_curve(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate drawdown curve (peak-to-trough declines)

        Returns daily portfolio value with drawdown percentage
        """
        # Build WHERE clause for date filtering
        where_conditions = ["status = 'CLOSED'", "exit_date IS NOT NULL"]
        params = []

        if start_date:
            where_conditions.append("exit_date >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("exit_date <= %s")
            params.append(end_date)

        where_clause = " AND ".join(where_conditions)

        # Query for daily P&L and calculate cumulative
        query = f"""
            WITH daily_pnl AS (
                SELECT
                    DATE(exit_date) as date,
                    SUM(actual_pnl) as daily_realized_pnl
                FROM trade_journal
                WHERE {where_clause}
                GROUP BY DATE(exit_date)
                ORDER BY DATE(exit_date)
            ),
            cumulative AS (
                SELECT
                    date,
                    daily_realized_pnl,
                    SUM(daily_realized_pnl) OVER (ORDER BY date) as portfolio_value
                FROM daily_pnl
            )
            SELECT
                date,
                portfolio_value,
                MAX(portfolio_value) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as peak_value
            FROM cumulative
            ORDER BY date
        """

        results = self.db.execute_query(query, tuple(params) if params else None)

        # Calculate drawdown percentage
        drawdown_curve = []
        for row in results:
            portfolio_value = float(row['portfolio_value']) if row['portfolio_value'] else 0.0
            peak_value = float(row['peak_value']) if row['peak_value'] else 0.0

            drawdown_pct = 0.0
            if peak_value > 0:
                drawdown_pct = ((portfolio_value - peak_value) / peak_value) * 100

            drawdown_curve.append({
                'date': row['date'].isoformat() if isinstance(row['date'], date) else row['date'],
                'portfolio_value': portfolio_value,
                'peak_value': peak_value,
                'drawdown_pct': round(drawdown_pct, 2)
            })

        return drawdown_curve
