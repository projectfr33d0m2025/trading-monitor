#!/usr/bin/env python3
"""
Create Production Tables Script
Creates trade_journal, order_execution, and position_tracking tables in production database.

IMPORTANT: This script does NOT create the analysis_decision table!
           That table already exists in your NocoDB instance.
           You must manually add 4 fields to it via the NocoDB UI.

Usage:
    python scripts/create_production_tables.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_layer import TradingDB
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_production_tables():
    """
    Create new tables for production NocoDB database
    Does NOT create analysis_decision (it already exists)
    """

    logger.info("Connecting to production PostgreSQL database...")

    try:
        # Connect to production database (test_mode=False)
        db = TradingDB(test_mode=False)

        logger.info("Creating production tables...")

        # Create only the NEW tables (not analysis_decision!)
        schema_sql = """
        -- Create trade_journal table
        CREATE TABLE IF NOT EXISTS trade_journal (
            id SERIAL PRIMARY KEY,
            trade_id VARCHAR(50) UNIQUE NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            trade_style VARCHAR(20) NOT NULL,
            pattern VARCHAR(50),
            status VARCHAR(20) NOT NULL DEFAULT 'ORDERED',
            initial_analysis_id VARCHAR(255),
            planned_entry DECIMAL(10,2) NOT NULL,
            planned_stop_loss DECIMAL(10,2) NOT NULL,
            planned_take_profit DECIMAL(10,2),
            planned_qty INT NOT NULL,
            actual_entry DECIMAL(10,2),
            actual_qty INT,
            current_stop_loss DECIMAL(10,2),
            days_open INT DEFAULT 0,
            last_review_date DATE,
            exit_date DATE,
            exit_price DECIMAL(10,2),
            actual_pnl DECIMAL(10,2),
            exit_reason VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        -- Create order_execution table
        CREATE TABLE IF NOT EXISTS order_execution (
            id SERIAL PRIMARY KEY,
            trade_journal_id INT NOT NULL,
            analysis_decision_id VARCHAR(255),
            alpaca_order_id VARCHAR(255) NOT NULL,
            client_order_id VARCHAR(255),
            order_type VARCHAR(50) NOT NULL,
            side VARCHAR(10) NOT NULL,
            order_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            time_in_force VARCHAR(10) NOT NULL,
            qty INT NOT NULL,
            limit_price DECIMAL(10,2),
            stop_price DECIMAL(10,2),
            filled_qty INT,
            filled_avg_price DECIMAL(10,2),
            filled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );

        -- Create position_tracking table
        CREATE TABLE IF NOT EXISTS position_tracking (
            id SERIAL PRIMARY KEY,
            trade_journal_id INT NOT NULL UNIQUE,
            symbol VARCHAR(50) NOT NULL,
            qty INT NOT NULL,
            avg_entry_price DECIMAL(10,2) NOT NULL,
            current_price DECIMAL(10,2) NOT NULL,
            market_value DECIMAL(10,2) NOT NULL,
            cost_basis DECIMAL(10,2) NOT NULL,
            unrealized_pnl DECIMAL(10,2) DEFAULT 0,
            stop_loss_order_id VARCHAR(255),
            take_profit_order_id VARCHAR(255),
            last_updated TIMESTAMP DEFAULT NOW()
        );

        -- Create indices
        CREATE INDEX IF NOT EXISTS idx_trade_journal_status ON trade_journal(status);
        CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol);
        CREATE INDEX IF NOT EXISTS idx_trade_journal_analysis_id ON trade_journal(initial_analysis_id);
        CREATE INDEX IF NOT EXISTS idx_order_execution_status ON order_execution(order_status);
        CREATE INDEX IF NOT EXISTS idx_order_execution_trade_journal ON order_execution(trade_journal_id);
        CREATE INDEX IF NOT EXISTS idx_position_tracking_symbol ON position_tracking(symbol);
        CREATE INDEX IF NOT EXISTS idx_position_tracking_trade_journal ON position_tracking(trade_journal_id);
        """

        with db.conn.cursor() as cursor:
            cursor.execute(schema_sql)
            db.conn.commit()

        logger.info("✅ Successfully created production tables!")
        logger.info("")
        logger.info("Tables created:")
        logger.info("  - trade_journal")
        logger.info("  - order_execution")
        logger.info("  - position_tracking")
        logger.info("")
        logger.info("Indices created: 7")
        logger.info("")
        logger.info("REMINDER: You must manually add 4 fields to the existing 'analysis_decision' table via NocoDB UI:")
        logger.info("  1. existing_order_id (SingleLineText)")
        logger.info("  2. existing_trade_journal_id (Number)")
        logger.info("  3. executed (Checkbox, default: false)")
        logger.info("  4. execution_time (DateTime)")
        logger.info("")
        logger.info("See docs/database-setup.md for detailed instructions.")

        # Verify tables were created
        logger.info("")
        logger.info("Verifying tables...")
        tables = db.execute_query("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('trade_journal', 'order_execution', 'position_tracking')
        """)

        table_names = [t['table_name'] for t in tables]
        logger.info(f"Found {len(table_names)} tables: {', '.join(table_names)}")

        if len(table_names) == 3:
            logger.info("✅ All tables verified successfully!")
        else:
            logger.warning(f"⚠️  Expected 3 tables but found {len(table_names)}")

        db.close()

    except Exception as e:
        logger.error(f"❌ Error creating production tables: {e}")
        logger.error("")
        logger.error("Troubleshooting tips:")
        logger.error("  1. Check your .env file has correct PostgreSQL credentials")
        logger.error("  2. Ensure you can connect to the database")
        logger.error("  3. Verify your user has CREATE TABLE permissions")
        sys.exit(1)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Production Database Tables Creation Script")
    logger.info("=" * 60)
    logger.info("")
    logger.info("This script will create the following tables:")
    logger.info("  - trade_journal")
    logger.info("  - order_execution")
    logger.info("  - position_tracking")
    logger.info("")
    logger.info("⚠️  WARNING: This does NOT create the analysis_decision table!")
    logger.info("   That table already exists in your NocoDB instance.")
    logger.info("")

    response = input("Continue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        create_production_tables()
    else:
        logger.info("Operation cancelled.")
        sys.exit(0)
