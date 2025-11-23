"""
Database connection tests.

이 테스트는 실제 DB 연결 없이도 연결 로직과 예외 처리를 검증합니다.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock


class TestDatabaseConnection:
    """DatabaseConnection 클래스 테스트."""

    def test_build_connection_string_with_credentials(self):
        """자격 증명이 있는 경우 연결 문자열 생성을 테스트합니다."""
        from mcp_server.db.connection import DatabaseConnection

        db = DatabaseConnection(
            dsn="TEST_DSN",
            user="test_user",
            password="test_password",
        )
        conn_str = db._build_connection_string()

        assert "DSN=TEST_DSN" in conn_str
        assert "UID=test_user" in conn_str
        assert "PWD=test_password" in conn_str

    def test_build_connection_string_without_credentials(self):
        """자격 증명이 없는 경우 연결 문자열 생성을 테스트합니다."""
        from mcp_server.db.connection import DatabaseConnection

        db = DatabaseConnection(dsn="TEST_DSN")
        db.user = None
        db.password = None
        conn_str = db._build_connection_string()

        assert "DSN=TEST_DSN" in conn_str
        assert "UID" not in conn_str
        assert "PWD" not in conn_str

    def test_get_connection_success(self):
        """성공적인 연결을 테스트합니다."""
        from mcp_server.db.connection import DatabaseConnection

        mock_pyodbc = MagicMock()
        mock_conn = MagicMock()
        mock_pyodbc.connect.return_value = mock_conn

        with patch("mcp_server.db.connection._get_pyodbc", return_value=mock_pyodbc):
            db = DatabaseConnection(dsn="TEST_DSN")
            with db.get_connection() as conn:
                assert conn is mock_conn

            mock_pyodbc.connect.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_get_connection_failure(self):
        """연결 실패 시 DatabaseConnectionError가 발생하는지 테스트합니다."""
        from mcp_server.db.connection import DatabaseConnection, DatabaseConnectionError

        mock_pyodbc = MagicMock()
        mock_pyodbc.Error = Exception
        mock_pyodbc.connect.side_effect = mock_pyodbc.Error("Connection failed")

        with patch("mcp_server.db.connection._get_pyodbc", return_value=mock_pyodbc):
            db = DatabaseConnection(dsn="INVALID_DSN")
            with pytest.raises(DatabaseConnectionError) as exc_info:
                with db.get_connection():
                    pass

            assert "Failed to connect" in str(exc_info.value)

    def test_execute_query_success(self):
        """쿼리 실행 성공을 테스트합니다."""
        from mcp_server.db.connection import DatabaseConnection

        mock_pyodbc = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("row1",), ("row2",)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pyodbc.connect.return_value = mock_conn

        with patch("mcp_server.db.connection._get_pyodbc", return_value=mock_pyodbc):
            db = DatabaseConnection(dsn="TEST_DSN")
            result = db.execute_query("SELECT * FROM test WHERE id = ?", (1,))

            assert len(result) == 2
            mock_cursor.execute.assert_called_once_with("SELECT * FROM test WHERE id = ?", (1,))

    def test_execute_query_as_dicts(self):
        """쿼리 결과를 딕셔너리 리스트로 반환하는지 테스트합니다."""
        from mcp_server.db.connection import DatabaseConnection

        mock_pyodbc = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "test1"), (2, "test2")]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pyodbc.connect.return_value = mock_conn

        with patch("mcp_server.db.connection._get_pyodbc", return_value=mock_pyodbc):
            db = DatabaseConnection(dsn="TEST_DSN")
            result = db.execute_query_as_dicts("SELECT * FROM test")

            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[0]["name"] == "test1"
            assert result[1]["id"] == 2
            assert result[1]["name"] == "test2"

    def test_execute_query_failure(self):
        """쿼리 실행 실패 시 DatabaseQueryError가 발생하는지 테스트합니다."""
        from mcp_server.db.connection import DatabaseConnection, DatabaseQueryError

        mock_pyodbc = MagicMock()
        mock_pyodbc.Error = Exception
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = mock_pyodbc.Error("Query failed")
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pyodbc.connect.return_value = mock_conn

        with patch("mcp_server.db.connection._get_pyodbc", return_value=mock_pyodbc):
            db = DatabaseConnection(dsn="TEST_DSN")
            with pytest.raises(DatabaseQueryError) as exc_info:
                db.execute_query("INVALID SQL")

            assert "Query execution failed" in str(exc_info.value)


class TestGetConnection:
    """get_connection 함수 테스트."""

    def test_get_connection_returns_singleton(self, reset_db_connection):
        """get_connection이 싱글톤을 반환하는지 테스트합니다."""
        from mcp_server.db.connection import get_connection

        conn1 = get_connection()
        conn2 = get_connection()
        assert conn1 is conn2

    def test_get_connection_returns_database_connection(self, reset_db_connection):
        """get_connection이 DatabaseConnection 인스턴스를 반환하는지 테스트합니다."""
        from mcp_server.db.connection import get_connection, DatabaseConnection

        conn = get_connection()
        assert isinstance(conn, DatabaseConnection)
