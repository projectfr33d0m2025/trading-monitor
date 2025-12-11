"""
PostgreSQL Database Abstraction Layer
Connects directly to Postgres DB underneath NocoDB
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import register_adapter, AsIs
import logging
import os
from uuid import UUID
from .config import get_postgres_config

logger = logging.getLogger(__name__)

# Register UUID adapter for psycopg2
# Alpaca API returns UUID objects which need to be adapted for PostgreSQL
register_adapter(UUID, lambda val: AsIs(f"'{val}'"))


class TradingDB:
    def __init__(self, test_mode=False):
        """
        Initialize database connection using environment variables

        Args:
            test_mode (bool): If True, use TEST_ prefixed environment variables
        """
        self.test_mode = test_mode
        config = get_postgres_config(test_mode)

        self.schema = config['schema']
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
            # Set search_path to use the configured schema
            with self.conn.cursor() as cursor:
                cursor.execute(f"SET search_path TO {self.schema}")
                self.conn.commit()
            logger.info(f"Database connected successfully (schema: {self.schema})")
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
        # Quote column names to preserve case sensitivity in PostgreSQL
        columns = ', '.join([f'"{col}"' for col in data.keys()])
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
        # Quote column names to preserve case sensitivity in PostgreSQL
        set_clause = ', '.join([f'"{k}" = %s' for k in data.keys()])
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

    def query(self, table, where_clause=None, params=None, order_by=None, limit=None, offset=None):
        """
        Query table with optional WHERE clause, ordering, and pagination

        Args:
            table (str): Table name
            where_clause (str): WHERE clause (without WHERE keyword)
            params (tuple): Query parameters
            order_by (str): ORDER BY clause (e.g., "created_at DESC")
            limit (int): Maximum number of records to return
            offset (int): Number of records to skip

        Returns:
            list: List of dictionaries representing rows
        """
        query = f"SELECT * FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        return self.execute_query(query, params)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
