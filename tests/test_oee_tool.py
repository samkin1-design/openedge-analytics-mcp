"""
OEE Tool tests.

DB를 mock하여 MCP Tool이 올바른 JSON 스키마를 반환하는지 테스트합니다.
"""

import pytest
from unittest.mock import patch, MagicMock

from mcp_server.tools.oee_tools import get_oee_trend, validate_date_format


class TestValidateDateFormat:
    """날짜 형식 검증 함수 테스트."""

    def test_valid_date(self):
        """유효한 날짜 형식을 테스트합니다."""
        assert validate_date_format("2024-01-01") is True
        assert validate_date_format("2024-12-31") is True

    def test_invalid_date_format(self):
        """잘못된 날짜 형식을 테스트합니다."""
        assert validate_date_format("2024/01/01") is False
        assert validate_date_format("01-01-2024") is False
        assert validate_date_format("2024-1-1") is False

    def test_invalid_date_value(self):
        """존재하지 않는 날짜를 테스트합니다."""
        assert validate_date_format("2024-13-01") is False
        assert validate_date_format("2024-02-30") is False


class TestGetOeeTrend:
    """get_oee_trend 함수 테스트."""

    def test_missing_line_id(self):
        """line_id가 없을 때 ValueError가 발생하는지 테스트합니다."""
        with pytest.raises(ValueError) as exc_info:
            get_oee_trend(
                line_id="",
                from_date="2024-01-01",
                to_date="2024-03-31",
            )
        assert "line_id is required" in str(exc_info.value)

    def test_invalid_from_date(self):
        """잘못된 from_date 형식에 대해 ValueError가 발생하는지 테스트합니다."""
        with pytest.raises(ValueError) as exc_info:
            get_oee_trend(
                line_id="LINE_01",
                from_date="invalid-date",
                to_date="2024-03-31",
            )
        assert "from_date must be in YYYY-MM-DD format" in str(exc_info.value)

    def test_invalid_to_date(self):
        """잘못된 to_date 형식에 대해 ValueError가 발생하는지 테스트합니다."""
        with pytest.raises(ValueError) as exc_info:
            get_oee_trend(
                line_id="LINE_01",
                from_date="2024-01-01",
                to_date="invalid-date",
            )
        assert "to_date must be in YYYY-MM-DD format" in str(exc_info.value)

    def test_from_date_after_to_date(self):
        """from_date가 to_date보다 클 때 ValueError가 발생하는지 테스트합니다."""
        with pytest.raises(ValueError) as exc_info:
            get_oee_trend(
                line_id="LINE_01",
                from_date="2024-03-31",
                to_date="2024-01-01",
            )
        assert "from_date must be less than or equal to to_date" in str(exc_info.value)

    @patch("mcp_server.tools.oee_tools.get_connection")
    @patch("mcp_server.tools.oee_tools.load_sql_template")
    def test_successful_query(self, mock_load_template, mock_get_conn):
        """성공적인 쿼리 실행과 JSON 스키마를 테스트합니다."""
        # Mock SQL template
        mock_load_template.return_value = """
            SELECT production_date, oee, availability, performance, quality
            FROM {schema}.oee_daily_metrics
            WHERE line_id = ? AND production_date >= ? AND production_date <= ?
        """

        # Mock database response (OpenEdge returns UPPERCASE column names)
        mock_db = MagicMock()
        mock_db.execute_query_as_dicts.return_value = [
            {
                "PRODUCTION_DATE": "2024-01-01",
                "OEE": 0.71,
                "AVAILABILITY": 0.9,
                "PERFORMANCE": 0.8,
                "QUALITY": 0.98,
            },
            {
                "PRODUCTION_DATE": "2024-01-02",
                "OEE": 0.75,
                "AVAILABILITY": 0.92,
                "PERFORMANCE": 0.82,
                "QUALITY": 0.99,
            },
        ]
        mock_get_conn.return_value = mock_db

        # Execute
        result = get_oee_trend(
            line_id="LINE_01",
            from_date="2024-01-01",
            to_date="2024-01-31",
        )

        # Verify response structure
        assert "line_id" in result
        assert result["line_id"] == "LINE_01"
        assert "from_date" in result
        assert result["from_date"] == "2024-01-01"
        assert "to_date" in result
        assert result["to_date"] == "2024-01-31"
        assert "rows" in result
        assert len(result["rows"]) == 2

        # Verify row structure
        row = result["rows"][0]
        assert "date" in row
        assert "oee" in row
        assert "availability" in row
        assert "performance" in row
        assert "quality" in row

        # Verify row values
        assert row["date"] == "2024-01-01"
        assert row["oee"] == 0.71
        assert row["availability"] == 0.9
        assert row["performance"] == 0.8
        assert row["quality"] == 0.98

    @patch("mcp_server.tools.oee_tools.get_connection")
    @patch("mcp_server.tools.oee_tools.load_sql_template")
    def test_empty_result(self, mock_load_template, mock_get_conn):
        """결과가 없는 경우 빈 rows를 반환하는지 테스트합니다."""
        mock_load_template.return_value = "SELECT * FROM {schema}.test"
        mock_db = MagicMock()
        mock_db.execute_query_as_dicts.return_value = []
        mock_get_conn.return_value = mock_db

        result = get_oee_trend(
            line_id="LINE_99",
            from_date="2024-01-01",
            to_date="2024-01-31",
        )

        assert result["rows"] == []
        assert result["line_id"] == "LINE_99"

    @patch("mcp_server.tools.oee_tools.load_sql_template")
    def test_sql_template_not_found(self, mock_load_template):
        """SQL 템플릿 파일이 없을 때 ValueError가 발생하는지 테스트합니다."""
        mock_load_template.side_effect = FileNotFoundError("Template not found")

        with pytest.raises(ValueError) as exc_info:
            get_oee_trend(
                line_id="LINE_01",
                from_date="2024-01-01",
                to_date="2024-03-31",
            )

        assert "SQL template not found" in str(exc_info.value)


class TestOeeToolResponseSchema:
    """OEE Tool 응답 JSON 스키마 테스트."""

    @patch("mcp_server.tools.oee_tools.get_connection")
    @patch("mcp_server.tools.oee_tools.load_sql_template")
    def test_response_schema_fields(self, mock_load_template, mock_get_conn):
        """응답이 필수 필드를 모두 포함하는지 테스트합니다."""
        mock_load_template.return_value = "SELECT * FROM {schema}.test"
        mock_db = MagicMock()
        mock_db.execute_query_as_dicts.return_value = [
            {
                "PRODUCTION_DATE": "2024-01-01",
                "OEE": 0.85,
                "AVAILABILITY": 0.95,
                "PERFORMANCE": 0.90,
                "QUALITY": 0.99,
            }
        ]
        mock_get_conn.return_value = mock_db

        result = get_oee_trend(
            line_id="LINE01",
            from_date="2024-01-01",
            to_date="2024-01-31",
        )

        # Top-level required fields
        required_fields = ["line_id", "from_date", "to_date", "rows"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Row required fields
        row_required_fields = ["date", "oee", "availability", "performance", "quality"]
        for row in result["rows"]:
            for field in row_required_fields:
                assert field in row, f"Missing required row field: {field}"

    @patch("mcp_server.tools.oee_tools.get_connection")
    @patch("mcp_server.tools.oee_tools.load_sql_template")
    def test_response_field_types(self, mock_load_template, mock_get_conn):
        """응답 필드의 타입이 올바른지 테스트합니다."""
        mock_load_template.return_value = "SELECT * FROM {schema}.test"
        mock_db = MagicMock()
        mock_db.execute_query_as_dicts.return_value = [
            {
                "PRODUCTION_DATE": "2024-01-01",
                "OEE": 0.85,
                "AVAILABILITY": 0.95,
                "PERFORMANCE": 0.90,
                "QUALITY": 0.99,
            }
        ]
        mock_get_conn.return_value = mock_db

        result = get_oee_trend(
            line_id="LINE01",
            from_date="2024-01-01",
            to_date="2024-01-31",
        )

        # Verify types
        assert isinstance(result["line_id"], str)
        assert isinstance(result["from_date"], str)
        assert isinstance(result["to_date"], str)
        assert isinstance(result["rows"], list)

        row = result["rows"][0]
        assert isinstance(row["date"], str)
        assert isinstance(row["oee"], float)
        assert isinstance(row["availability"], float)
        assert isinstance(row["performance"], float)
        assert isinstance(row["quality"], float)
