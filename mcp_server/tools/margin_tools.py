"""
마진(Margin) 분석 관련 MCP Tools.

이 모듈은 고객별 매출/원가/마진 데이터를 조회하는 read-only 툴을 제공합니다.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from mcp_server.config import get_config, load_sql_template
from mcp_server.db.connection import (
    get_connection,
    DatabaseConnectionError,
    DatabaseQueryError,
)

logger = logging.getLogger(__name__)


def validate_period_format(period: str) -> bool:
    """
    Validate period format.

    Accepts:
        - Monthly: 'YYYY-MM' (e.g., '2024-01')
        - Quarterly: 'YYYYQN' (e.g., '2024Q1')
        - Yearly: 'YYYY' (e.g., '2024')

    Args:
        period: Period string to validate.

    Returns:
        True if valid, False otherwise.
    """
    patterns = [
        r"^\d{4}-\d{2}$",    # Monthly: YYYY-MM
        r"^\d{4}Q[1-4]$",    # Quarterly: YYYYQN
        r"^\d{4}$",          # Yearly: YYYY
    ]
    return any(re.match(pattern, period) for pattern in patterns)


def get_margin_by_customer(
    period: str,
    customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    특정 기간 동안 고객별 매출, 원가, 마진 요약을 조회합니다.

    Args:
        period: 조회 기간 (예: '2024-01', '2024Q1', '2024')
            - 'YYYY-MM': 월별 조회
            - 'YYYYQN': 분기별 조회 (Q1~Q4)
            - 'YYYY': 연간 조회
        customer_id: 고객 ID (선택사항, 없으면 전체 고객 요약)

    Returns:
        마진 요약 데이터를 담은 딕셔너리:
        {
            "period": str,
            "customer_id": str | None,
            "rows": [
                {
                    "customer_id": str,
                    "sales_amount": float,
                    "cogs_amount": float,
                    "margin_amount": float,
                    "margin_rate": float (0.0 ~ 1.0)
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
    if not period or not validate_period_format(period):
        raise ValueError(
            "period must be in one of these formats: 'YYYY-MM', 'YYYYQN', or 'YYYY'"
        )

    # customer_id 가 빈 문자열인 경우 None 처리
    if customer_id is not None and not customer_id.strip():
        customer_id = None

    logger.info(
        f"Fetching margin summary for period={period}, customer_id={customer_id}"
    )

    try:
        # Load SQL template
        config = get_config()
        sql_template = load_sql_template("margin_by_customer.sql")

        # Replace schema placeholder
        sql = sql_template.replace("{schema}", config.analytics_schema)

        # Build parameters - customer_id 조건 처리
        # SQL 템플릿에서 customer_id 필터링을 처리하도록 함
        if customer_id is not None:
            sql = sql.replace("{customer_filter}", "AND customer_id = ?")
            params = (period, customer_id)
        else:
            sql = sql.replace("{customer_filter}", "")
            params = (period,)

        # Execute query with parameter binding
        db = get_connection()
        rows = db.execute_query_as_dicts(sql, params)

        # Format results
        result_rows: List[Dict[str, Any]] = []
        for row in rows:
            sales_amount = float(row.get("sales_amount", 0.0))
            cogs_amount = float(row.get("cogs_amount", 0.0))
            margin_amount = sales_amount - cogs_amount

            # Calculate margin_rate (handle division by zero)
            margin_rate = 0.0
            if sales_amount > 0:
                margin_rate = margin_amount / sales_amount

            result_rows.append({
                "customer_id": str(row.get("customer_id", "")),
                "sales_amount": round(sales_amount, 2),
                "cogs_amount": round(cogs_amount, 2),
                "margin_amount": round(margin_amount, 2),
                "margin_rate": round(margin_rate, 4),
            })

        return {
            "period": period,
            "customer_id": customer_id,
            "rows": result_rows,
        }

    except FileNotFoundError as e:
        logger.error(f"SQL template not found: {e}")
        raise ValueError(f"SQL template not found: {e}")
    except (DatabaseConnectionError, DatabaseQueryError) as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_margin_by_customer: {e}")
        raise
