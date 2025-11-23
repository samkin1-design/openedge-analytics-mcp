"""
ODBC Database connection module for OpenEdge Analytics.

Provides connection management with context manager support.
"""

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, List, Optional, Tuple

from mcp_server.config import get_config

# Lazy import for pyodbc to allow testing without ODBC drivers
pyodbc = None


def _get_pyodbc():
    """Lazy load pyodbc module."""
    global pyodbc
    if pyodbc is None:
        import pyodbc as _pyodbc
        pyodbc = _pyodbc
    return pyodbc

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Exception raised for database connection errors."""
    pass


class DatabaseQueryError(Exception):
    """Exception raised for query execution errors."""
    pass


class DatabaseConnection:
    """
    ODBC Database connection wrapper with context manager support.

    Usage:
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table WHERE id = ?", (id_value,))
            rows = cursor.fetchall()
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize DatabaseConnection.

        Args:
            dsn: ODBC DSN name. Defaults to config value.
            user: Database username. Defaults to config value.
            password: Database password. Defaults to config value.
            timeout: Connection timeout in seconds. Defaults to config value.
        """
        config = get_config()
        self.dsn = dsn or config.database.dsn
        self.user = user or config.database.user
        self.password = password or config.database.password
        self.timeout = timeout or config.database.timeout_seconds

    def _build_connection_string(self) -> str:
        """Build ODBC connection string."""
        parts = [f"DSN={self.dsn}"]
        if self.user:
            parts.append(f"UID={self.user}")
        if self.password:
            parts.append(f"PWD={self.password}")
        return ";".join(parts)

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """
        Get a database connection as a context manager.

        Yields:
            pyodbc.Connection: Database connection object.

        Raises:
            DatabaseConnectionError: If connection fails.
        """
        _pyodbc = _get_pyodbc()
        conn = None
        try:
            conn_str = self._build_connection_string()
            logger.debug(f"Connecting to DSN: {self.dsn}")
            conn = _pyodbc.connect(conn_str, timeout=self.timeout)
            conn.timeout = self.timeout
            yield conn
        except _pyodbc.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
        finally:
            if conn is not None:
                try:
                    conn.close()
                    logger.debug("Database connection closed")
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")

    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """
        Get a database cursor as a context manager.

        Yields:
            pyodbc.Cursor: Database cursor object.

        Raises:
            DatabaseConnectionError: If connection fails.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> List[Any]:
        """
        Execute a read-only query and return all results.

        Args:
            query: SQL query string with ? placeholders for parameters.
            params: Tuple of parameter values for binding.

        Returns:
            List of result rows.

        Raises:
            DatabaseConnectionError: If connection fails.
            DatabaseQueryError: If query execution fails.
        """
        _pyodbc = _get_pyodbc()
        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except _pyodbc.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseQueryError(f"Query execution failed: {e}") from e

    def execute_query_as_dicts(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> List[dict]:
        """
        Execute a read-only query and return results as list of dictionaries.

        Args:
            query: SQL query string with ? placeholders for parameters.
            params: Tuple of parameter values for binding.

        Returns:
            List of result rows as dictionaries.

        Raises:
            DatabaseConnectionError: If connection fails.
            DatabaseQueryError: If query execution fails.
        """
        _pyodbc = _get_pyodbc()
        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except _pyodbc.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseQueryError(f"Query execution failed: {e}") from e


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_connection() -> DatabaseConnection:
    """
    Get the global DatabaseConnection instance.

    Returns:
        DatabaseConnection instance configured from environment.
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection
