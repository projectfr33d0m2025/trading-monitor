"""
PostgreSQL Database Abstraction Layer
Connects directly to Postgres DB underneath NocoDB
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
from config import get_postgres_config

logger = logging.getLogger(__name__)


class TradingDB:
    def __init__(self, test_mode=False):
        """
        Initialize database connection using environment variables

        Args:
            test_mode (bool): If True, use TEST_ prefixed environment variables
        """
        self.test_mode = test_mode
        config = get_postgres_config(test_mode)

        self.connection_string = (
            f"host={config['host']} "
            f"port={config['port']} "
            f"dbname={config['database']} "
            f"user={config['user']} "
            f"password={config['password']}"
        )
        self.conn = None
        self.connect()

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def execute_query(self, query, params=None):
        """
        Execute a SELECT query and return results as list of dicts
        Also handles INSERT/UPDATE/DELETE by detecting query type

        Args:
            query (str): SQL query
            params (tuple): Query parameters

        Returns:
            list: List of dictionaries for SELECT, or empty list for INSERT/UPDATE/DELETE
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                # Check if query is a SELECT (has results to fetch)
                if cursor.description:
                    return cursor.fetchall()
                else:
                    # For INSERT/UPDATE/DELETE
                    self.conn.commit()
                    return []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.conn.rollback()
            raise

    def execute_update(self, query, params=None):
        """
        Execute INSERT/UPDATE/DELETE and return affected rows

        Args:
            query (str): SQL INSERT/UPDATE/DELETE query
            params (tuple): Query parameters

        Returns:
            int: Number of affected rows
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            self.conn.rollback()
            raise

    def insert(self, table, data):
        """
        Insert a record and return the ID

        Args:
            table (str): Table name
            data (dict): Column-value pairs

        Returns:
            int: ID of inserted record
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, tuple(data.values()))
                self.conn.commit()
                return cursor.fetchone()['id']
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            self.conn.rollback()
            raise

    def update(self, table, record_id, data):
        """
        Update a record by ID

        Args:
            table (str): Table name
            record_id (int): Record ID
            data (dict): Column-value pairs to update

        Returns:
            bool: True if record was updated
        """
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = %s"
        params = tuple(data.values()) + (record_id,)

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self.conn.rollback()
            raise

    def get_by_id(self, table, record_id):
        """
        Get a single record by ID

        Args:
            table (str): Table name
            record_id (int): Record ID

        Returns:
            dict: Record data or None if not found
        """
        query = f"SELECT * FROM {table} WHERE id = %s"
        results = self.execute_query(query, (record_id,))
        return results[0] if results else None

    def query(self, table, where_clause=None, params=None):
        """
        Query table with optional WHERE clause

        Args:
            table (str): Table name
            where_clause (str): WHERE clause (without WHERE keyword)
            params (tuple): Query parameters

        Returns:
            list: List of dictionaries representing rows
        """
        query = f"SELECT * FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        return self.execute_query(query, params)

    def create_schema(self):
        """
        Create all required tables for testing/development
        Use this for test databases that start empty!
        For production NocoDB, manually add 4 fields to existing analysis_decision table.

        NOTE: No foreign key constraints as NocoDB doesn't support them.
        Relationships are managed at application level.
        """
        schema_sql = """
        -- Create analysis_decision table (for testing/dev only)
        CREATE TABLE IF NOT EXISTS analysis_decision (
            "Analysis Id" VARCHAR(255) PRIMARY KEY,
            "Date time" TIMESTAMP DEFAULT NOW(),
            "Ticker" VARCHAR(50) NOT NULL,
            "Chart" TEXT,
            "Analysis Prompt" TEXT,
            "3 Month Chart" TEXT,
            "Analysis" TEXT,
            "Trade Type" VARCHAR(50),
            "Decision" JSONB,
            "Approve" BOOLEAN DEFAULT false,
            "Date" DATE,
            "Remarks" TEXT,
            existing_order_id VARCHAR(255),
            existing_trade_journal_id INT,
            executed BOOLEAN DEFAULT false,
            execution_time TIMESTAMP
        );

        -- Create trade_journal table
        CREATE TABLE IF NOT EXISTS trade_journal (
            id SERIAL PRIMARY KEY,
            trade_id VARCHAR(50) UNIQUE NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            trade_style VARCHAR(20) {trade_style_constraint},
            pattern VARCHAR(50),
            status VARCHAR(20) NOT NULL DEFAULT 'ORDERED',
            initial_analysis_id VARCHAR(255),
            planned_entry DECIMAL(10,2) {planned_entry_constraint},
            planned_stop_loss DECIMAL(10,2) {planned_stop_loss_constraint},
            planned_take_profit DECIMAL(10,2),
            planned_qty INT {planned_qty_constraint},
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
            time_in_force VARCHAR(10) {time_in_force_constraint},
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
        CREATE INDEX IF NOT EXISTS idx_analysis_decision_executed ON analysis_decision(executed);
        CREATE INDEX IF NOT EXISTS idx_analysis_decision_ticker ON analysis_decision("Ticker");
        CREATE INDEX IF NOT EXISTS idx_trade_journal_status ON trade_journal(status);
        CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol);
        CREATE INDEX IF NOT EXISTS idx_trade_journal_analysis_id ON trade_journal(initial_analysis_id);
        CREATE INDEX IF NOT EXISTS idx_order_execution_status ON order_execution(order_status);
        CREATE INDEX IF NOT EXISTS idx_order_execution_trade_journal ON order_execution(trade_journal_id);
        CREATE INDEX IF NOT EXISTS idx_position_tracking_symbol ON position_tracking(symbol);
        CREATE INDEX IF NOT EXISTS idx_position_tracking_trade_journal ON position_tracking(trade_journal_id);
        """

        # Set constraints based on test mode
        # In test mode, allow nulls with defaults; in production, enforce NOT NULL
        if self.test_mode:
            constraints = {
                'trade_style_constraint': "DEFAULT 'SWING'",
                'planned_entry_constraint': "DEFAULT 0",
                'planned_stop_loss_constraint': "DEFAULT 0",
                'planned_qty_constraint': "DEFAULT 0",
                'time_in_force_constraint': "DEFAULT 'day'"
            }
        else:
            constraints = {
                'trade_style_constraint': "NOT NULL",
                'planned_entry_constraint': "NOT NULL",
                'planned_stop_loss_constraint': "NOT NULL",
                'planned_qty_constraint': "NOT NULL",
                'time_in_force_constraint': "NOT NULL"
            }

        # Format the schema SQL with constraints
        schema_sql = schema_sql.format(**constraints)

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(schema_sql)
                self.conn.commit()
                logger.info("Schema created successfully")
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            self.conn.rollback()
            raise

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
