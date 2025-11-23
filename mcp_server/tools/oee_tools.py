"""
OEE (Overall Equipment Effectiveness) 관련 MCP Tools.

이 모듈은 생산 라인의 OEE 데이터를 조회하는 read-only 툴을 제공합니다.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp_server.config import get_config, load_sql_template
from mcp_server.db.connection import (
    get_connection,
    DatabaseConnectionError,
    DatabaseQueryError,
)

logger = logging.getLogger(__name__)


def validate_date_format(date_str: str) -> bool:
    """
    Validate ISO date format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate.

    Returns:
        True if valid, False otherwise.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_oee_trend(
    line_id: str,
    from_date: str,
    to_date: str,
) -> Dict[str, Any]:
    """
    특정 라인(line_id)의 기간별 OEE 트렌드를 조회합니다.

    OEE(Overall Equipment Effectiveness)는 설비종합효율로,
    가용성(Availability) × 성능(Performance) × 품질(Quality)로 계산됩니다.

    Args:
        line_id: 생산 라인 ID (예: LINE_01)
        from_date: 조회 시작일 (ISO 날짜 형식: YYYY-MM-DD)
        to_date: 조회 종료일 (ISO 날짜 형식: YYYY-MM-DD)

    Returns:
        OEE 트렌드 데이터를 담은 딕셔너리:
        {
            "line_id": str,
            "from_date": str,
            "to_date": str,
            "rows": [
                {
                    "date": str (YYYY-MM-DD),
                    "oee": float (0.0 ~ 1.0),
                    "availability": float (0.0 ~ 1.0),
                    "performance": float (0.0 ~ 1.0),
                    "quality": float (0.0 ~ 1.0)
                },
                ...
            ]
        }

    Raises:
        ValueError: 파라미터가 유효하지 않은 경우
        DatabaseConnectionError: DB 연결 실패 시
        DatabaseQueryError: 쿼리 실행 실패 시
    """
    # Validate parameters
    if not line_id or not line_id.strip():
        raise ValueError("line_id is required")

    if not from_date or not validate_date_format(from_date):
        raise ValueError("from_date must be in YYYY-MM-DD format")

    if not to_date or not validate_date_format(to_date):
        raise ValueError("to_date must be in YYYY-MM-DD format")

    if from_date > to_date:
        raise ValueError("from_date must be less than or equal to to_date")

    logger.info(f"Fetching OEE trend for line={line_id}, period={from_date} to {to_date}")

    try:
        # Load SQL template
        config = get_config()
        sql_template = load_sql_template("oee_trend.sql")

        # Replace schema placeholder
        # Note: 스키마명은 파라미터 바인딩이 아닌 문자열 치환 사용
        # (대부분의 DB에서 스키마명은 파라미터로 전달 불가)
        sql = sql_template.replace("{schema}", config.analytics_schema)

        # Execute query with parameter binding
        db = get_connection()
        rows = db.execute_query_as_dicts(
            sql,
            (line_id, from_date, to_date),
        )

        # Format results
        result_rows: List[Dict[str, Any]] = []
        for row in rows:
            result_rows.append({
                "date": str(row.get("production_date", "")),
                "oee": float(row.get("oee", 0.0)),
                "availability": float(row.get("availability", 0.0)),
                "performance": float(row.get("performance", 0.0)),
                "quality": float(row.get("quality", 0.0)),
            })

        return {
            "line_id": line_id,
            "from_date": from_date,
            "to_date": to_date,
            "rows": result_rows,
        }

    except FileNotFoundError as e:
        logger.error(f"SQL template not found: {e}")
        raise ValueError(f"SQL template not found: {e}")
    except (DatabaseConnectionError, DatabaseQueryError) as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_oee_trend: {e}")
        raise
