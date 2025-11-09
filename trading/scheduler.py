#!/usr/bin/env python3
"""
Trading System Scheduler
Runs all trading programs on their defined schedules using APScheduler

Schedule:
- Order Executor: Once at 9:45 AM ET (Mon-Fri)
- Order Monitor: Every 5 min during trading hours (9:30 AM - 4:00 PM ET, Mon-Fri) + 6:00 PM ET
- Position Monitor: Every 10 min during trading hours (9:30 AM - 4:00 PM ET, Mon-Fri) + 6:15 PM ET
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from order_executor import OrderExecutor
from order_monitor import OrderMonitor
from position_monitor import PositionMonitor
import logging
import pytz
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# US Eastern timezone (NYSE trading hours)
eastern = pytz.timezone('US/Eastern')

# Create scheduler
scheduler = BlockingScheduler(timezone=eastern)


def run_order_executor():
    """Wrapper to run order executor"""
    try:
        logger.info("Starting Order Executor job...")
        executor = OrderExecutor()
        executor.run()
    except Exception as e:
        logger.error(f"Order Executor job failed: {e}", exc_info=True)


def run_order_monitor():
    """Wrapper to run order monitor"""
    try:
        logger.info("Starting Order Monitor job...")
        monitor = OrderMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Order Monitor job failed: {e}", exc_info=True)


def run_position_monitor():
    """Wrapper to run position monitor"""
    try:
        logger.info("Starting Position Monitor job...")
        monitor = PositionMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Position Monitor job failed: {e}", exc_info=True)


def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Shutdown signal received, stopping scheduler...")
    scheduler.shutdown(wait=False)
    sys.exit(0)


def setup_scheduler():
    """Configure all scheduled jobs"""

    # Program 2: Order Executor - Once at 9:45 AM ET (Mon-Fri)
    scheduler.add_job(
        run_order_executor,
        CronTrigger(
            day_of_week='mon-fri',
            hour=9,
            minute=45,
            timezone=eastern
        ),
        id='order_executor',
        name='Order Executor (9:45 AM ET)',
        max_instances=1,
        coalesce=True
    )

    # Program 3: Order Monitor - Every 5 minutes during trading hours (9:30 AM - 4:00 PM ET, Mon-Fri)
    scheduler.add_job(
        run_order_monitor,
        CronTrigger(
            day_of_week='mon-fri',
            hour='9-15',  # 9 AM to 3:59 PM
            minute='*/5',  # Every 5 minutes
            timezone=eastern
        ),
        id='order_monitor_trading',
        name='Order Monitor (every 5 min during trading)',
        max_instances=1,
        coalesce=True
    )

    # Program 3: Order Monitor - Once at 6:00 PM ET (Mon-Fri)
    scheduler.add_job(
        run_order_monitor,
        CronTrigger(
            day_of_week='mon-fri',
            hour=18,
            minute=0,
            timezone=eastern
        ),
        id='order_monitor_eod',
        name='Order Monitor (6:00 PM ET)',
        max_instances=1,
        coalesce=True
    )

    # Program 4: Position Monitor - Every 10 minutes during trading hours (9:30 AM - 4:00 PM ET, Mon-Fri)
    scheduler.add_job(
        run_position_monitor,
        CronTrigger(
            day_of_week='mon-fri',
            hour='9-15',  # 9 AM to 3:59 PM
            minute='*/10',  # Every 10 minutes
            timezone=eastern
        ),
        id='position_monitor_trading',
        name='Position Monitor (every 10 min during trading)',
        max_instances=1,
        coalesce=True
    )

    # Program 4: Position Monitor - Once at 6:15 PM ET (Mon-Fri)
    scheduler.add_job(
        run_position_monitor,
        CronTrigger(
            day_of_week='mon-fri',
            hour=18,
            minute=15,
            timezone=eastern
        ),
        id='position_monitor_eod',
        name='Position Monitor (6:15 PM ET)',
        max_instances=1,
        coalesce=True
    )


def main():
    """Main entry point"""
    logger.info("=" * 80)
    logger.info("Trading System Scheduler Starting")
    logger.info("=" * 80)
    logger.info("")

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Setup scheduled jobs
    setup_scheduler()

    # Display scheduled jobs
    logger.info("Scheduled jobs:")
    logger.info("")
    for job in scheduler.get_jobs():
        logger.info(f"  • {job.name}")
        logger.info(f"    ID: {job.id}")
        logger.info(f"    Trigger: {job.trigger}")
        logger.info(f"    Next run: {job.next_run_time}")
        logger.info("")

    logger.info("=" * 80)
    logger.info("Scheduler is running. Press Ctrl+C to stop.")
    logger.info("=" * 80)
    logger.info("")

    try:
        # Start the scheduler
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
