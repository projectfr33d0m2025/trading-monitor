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
import os
import pytz
import signal
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

    # Program 2: Order Executor - Once at configured time
    executor_hour = int(os.getenv('ORDER_EXECUTOR_HOUR', '9'))
    executor_minute = int(os.getenv('ORDER_EXECUTOR_MINUTE', '45'))
    executor_dow = os.getenv('ORDER_EXECUTOR_DAY_OF_WEEK', 'mon-fri')

    scheduler.add_job(
        run_order_executor,
        CronTrigger(
            day_of_week=executor_dow,
            hour=executor_hour,
            minute=executor_minute,
            timezone=eastern
        ),
        id='order_executor',
        name=f'Order Executor ({executor_hour}:{executor_minute:02d} ET)',
        max_instances=1,
        coalesce=True
    )

    # Program 3: Order Monitor - During trading hours
    om_trading_hours = os.getenv('ORDER_MONITOR_TRADING_HOURS', '9-15')
    om_trading_interval = os.getenv('ORDER_MONITOR_TRADING_INTERVAL', '*/5')
    om_trading_dow = os.getenv('ORDER_MONITOR_TRADING_DOW', 'mon-fri')

    scheduler.add_job(
        run_order_monitor,
        CronTrigger(
            day_of_week=om_trading_dow,
            hour=om_trading_hours,
            minute=om_trading_interval,
            timezone=eastern
        ),
        id='order_monitor_trading',
        name=f'Order Monitor ({om_trading_interval} min, hours {om_trading_hours} ET)',
        max_instances=1,
        coalesce=True
    )

    # Program 3: Order Monitor - End of day check
    om_eod_hour = int(os.getenv('ORDER_MONITOR_EOD_HOUR', '18'))
    om_eod_minute = int(os.getenv('ORDER_MONITOR_EOD_MINUTE', '0'))
    om_eod_dow = os.getenv('ORDER_MONITOR_EOD_DOW', 'mon-fri')

    scheduler.add_job(
        run_order_monitor,
        CronTrigger(
            day_of_week=om_eod_dow,
            hour=om_eod_hour,
            minute=om_eod_minute,
            timezone=eastern
        ),
        id='order_monitor_eod',
        name=f'Order Monitor EOD ({om_eod_hour}:{om_eod_minute:02d} ET)',
        max_instances=1,
        coalesce=True
    )

    # Program 4: Position Monitor - During trading hours
    pm_trading_hours = os.getenv('POSITION_MONITOR_TRADING_HOURS', '9-15')
    pm_trading_interval = os.getenv('POSITION_MONITOR_TRADING_INTERVAL', '*/10')
    pm_trading_dow = os.getenv('POSITION_MONITOR_TRADING_DOW', 'mon-fri')

    scheduler.add_job(
        run_position_monitor,
        CronTrigger(
            day_of_week=pm_trading_dow,
            hour=pm_trading_hours,
            minute=pm_trading_interval,
            timezone=eastern
        ),
        id='position_monitor_trading',
        name=f'Position Monitor ({pm_trading_interval} min, hours {pm_trading_hours} ET)',
        max_instances=1,
        coalesce=True
    )

    # Program 4: Position Monitor - End of day check
    pm_eod_hour = int(os.getenv('POSITION_MONITOR_EOD_HOUR', '18'))
    pm_eod_minute = int(os.getenv('POSITION_MONITOR_EOD_MINUTE', '15'))
    pm_eod_dow = os.getenv('POSITION_MONITOR_EOD_DOW', 'mon-fri')

    scheduler.add_job(
        run_position_monitor,
        CronTrigger(
            day_of_week=pm_eod_dow,
            hour=pm_eod_hour,
            minute=pm_eod_minute,
            timezone=eastern
        ),
        id='position_monitor_eod',
        name=f'Position Monitor EOD ({pm_eod_hour}:{pm_eod_minute:02d} ET)',
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
        # Next run time is calculated after scheduler starts
        next_run = getattr(job, 'next_run_time', 'Will be calculated on start')
        logger.info(f"    Next run: {next_run}")
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
