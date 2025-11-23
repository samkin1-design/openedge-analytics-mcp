"""
Scrap(불량) 분석 관련 MCP Tools.

이 모듈은 공장의 Scrap 데이터를 조회하는 read-only 툴을 제공합니다.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal

from mcp_server.config import get_config, load_sql_template
from mcp_server.db.connection import (
    get_connection,
    DatabaseConnectionError,
    DatabaseQueryError,
)

logger = logging.getLogger(__name__)


# 허용된 group_by 값들
VALID_GROUP_BY = {"product", "workcenter", "operation"}

# group_by 값에 따른 SQL 컬럼 매핑 (QAD op_hist 테이블 기준)
GROUP_BY_COLUMNS = {
    "product": "op_part",       # 품목별
    "workcenter": "op_wkctr",   # 작업장별
    "operation": "op_wo_op",    # 공정별
}


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


def get_scrap_summary(
    plant_id: str,
    from_date: str,
    to_date: str,
    group_by: str,
) -> Dict[str, Any]:
    """
    특정 공장(plant_id)의 기간별 Scrap 요약을 조회합니다.

    Args:
        plant_id: 공장 ID (예: PLANT_A)
        from_date: 조회 시작일 (ISO 날짜 형식: YYYY-MM-DD)
        to_date: 조회 종료일 (ISO 날짜 형식: YYYY-MM-DD)
        group_by: 그룹화 기준 ('product', 'workcenter', 'operation' 중 하나)

    Returns:
        Scrap 요약 데이터를 담은 딕셔너리:
        {
            "plant_id": str,
            "from_date": str,
            "to_date": str,
            "group_by": str,
            "rows": [
                {
                    "group_key": str,
                    "produced_qty": float,
                    "scrap_qty": float,
                    "scrap_rate": float (0.0 ~ 1.0)
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
    if not plant_id or not plant_id.strip():
        raise ValueError("plant_id is required")

    if not from_date or not validate_date_format(from_date):
        raise ValueError("from_date must be in YYYY-MM-DD format")

    if not to_date or not validate_date_format(to_date):
        raise ValueError("to_date must be in YYYY-MM-DD format")

    if from_date > to_date:
        raise ValueError("from_date must be less than or equal to to_date")

    if group_by not in VALID_GROUP_BY:
        raise ValueError(f"group_by must be one of: {', '.join(VALID_GROUP_BY)}")

    logger.info(
        f"Fetching scrap summary for plant={plant_id}, "
        f"period={from_date} to {to_date}, group_by={group_by}"
    )

    try:
        # Load SQL template
        config = get_config()
        sql_template = load_sql_template("scrap_summary.sql")

        # Replace placeholders
        # Note: 스키마명과 컬럼명은 파라미터 바인딩이 아닌 문자열 치환 사용
        group_column = GROUP_BY_COLUMNS[group_by]
        sql = sql_template.replace("{schema}", config.analytics_schema)
        sql = sql.replace("{group_column}", group_column)

        # Execute query with parameter binding
        db = get_connection()
        rows = db.execute_query_as_dicts(
            sql,
            (plant_id, from_date, to_date),
        )

        # Format results
        result_rows: List[Dict[str, Any]] = []
        for row in rows:
            produced_qty = float(row.get("produced_qty", 0.0))
            scrap_qty = float(row.get("scrap_qty", 0.0))

            # Calculate scrap_rate (handle division by zero)
            scrap_rate = 0.0
            if produced_qty > 0:
                scrap_rate = scrap_qty / produced_qty

            result_rows.append({
                "group_key": str(row.get("group_key", "")),
                "produced_qty": produced_qty,
                "scrap_qty": scrap_qty,
                "scrap_rate": round(scrap_rate, 6),
            })

        return {
            "plant_id": plant_id,
            "from_date": from_date,
            "to_date": to_date,
            "group_by": group_by,
            "rows": result_rows,
        }

    except FileNotFoundError as e:
        logger.error(f"SQL template not found: {e}")
        raise ValueError(f"SQL template not found: {e}")
    except (DatabaseConnectionError, DatabaseQueryError) as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_scrap_summary: {e}")
        raise
