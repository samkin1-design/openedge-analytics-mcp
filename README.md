# OpenEdge Analytics MCP Server

QAD/OpenEdge 데이터베이스의 Analytics Mart 스키마에 연결하여 분석용 데이터를 제공하는 **Read-Only MCP 서버**입니다.

## 개요

이 MCP(Model Context Protocol) 서버는 LangGraph, ChatGPT 등의 AI 클라이언트가 도메인 분석 툴로 사용할 수 있도록 설계되었습니다.

### 주요 특징

- **Read-Only**: 데이터 조회만 가능, 쓰기/수정 작업 없음
- **Analytics 전용**: OEE, Scrap, Margin 등 분석 지표 조회
- **SQL 템플릿 분리**: SQL 쿼리를 별도 파일로 관리하여 유지보수 용이
- **파라미터 바인딩**: SQL Injection 방지를 위한 안전한 쿼리 실행

## 요구사항

- **Python**: 3.10 이상
- **ODBC Driver**: OpenEdge ODBC 드라이버 설치 필요
- **DSN 설정**: 시스템 또는 사용자 ODBC DSN 구성 필요

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd openedge-analytics-mcp
```

### 2. 가상환경 생성 (권장)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate     # Windows
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열고 실제 값으로 수정:

```env
ODBC_DSN=QAD_OPENEDGE_ANALYTICS
DB_USER=your_username
DB_PASSWORD=your_password
DB_TIMEOUT_SECONDS=30
ANALYTICS_SCHEMA=ANALYTICS_MART
```

## MCP 서버 기동

```bash
python -m mcp_server.server
```

서버는 표준 입력/출력(stdin/stdout)을 통해 JSON-RPC 프로토콜로 통신합니다.

## 사용 가능한 MCP Tools

### 1. `get_oee_trend`

특정 생산 라인의 기간별 OEE(Overall Equipment Effectiveness) 트렌드를 조회합니다.

**파라미터:**
| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `line_id` | string | O | 생산 라인 ID (예: LINE_01) |
| `from_date` | string | O | 조회 시작일 (YYYY-MM-DD) |
| `to_date` | string | O | 조회 종료일 (YYYY-MM-DD) |

**반환 예시:**
```json
{
  "line_id": "LINE_01",
  "from_date": "2024-01-01",
  "to_date": "2024-03-31",
  "rows": [
    {
      "date": "2024-01-01",
      "oee": 0.71,
      "availability": 0.9,
      "performance": 0.8,
      "quality": 0.98
    }
  ]
}
```

### 2. `get_scrap_summary`

특정 공장의 기간별 Scrap(불량) 요약을 조회합니다.

**파라미터:**
| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `plant_id` | string | O | 공장 ID (예: PLANT_A) |
| `from_date` | string | O | 조회 시작일 (YYYY-MM-DD) |
| `to_date` | string | O | 조회 종료일 (YYYY-MM-DD) |
| `group_by` | string | O | 그룹화 기준 (product/workcenter/operation) |

**반환 예시:**
```json
{
  "plant_id": "PLANT_A",
  "from_date": "2024-01-01",
  "to_date": "2024-01-31",
  "group_by": "product",
  "rows": [
    {
      "group_key": "2AM051B",
      "produced_qty": 1000,
      "scrap_qty": 35,
      "scrap_rate": 0.035
    }
  ]
}
```

### 3. `get_margin_by_customer`

특정 기간 동안 고객별 매출/원가/마진 요약을 조회합니다.

**파라미터:**
| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `period` | string | O | 조회 기간 (YYYY-MM, YYYYQN, YYYY) |
| `customer_id` | string | X | 고객 ID (없으면 전체 고객) |

**반환 예시:**
```json
{
  "period": "2024-01",
  "customer_id": null,
  "rows": [
    {
      "customer_id": "BMW",
      "sales_amount": 100000.0,
      "cogs_amount": 72000.0,
      "margin_amount": 28000.0,
      "margin_rate": 0.28
    }
  ]
}
```

## 프로젝트 구조

```
openedge-analytics-mcp/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py           # MCP 서버 진입점
│   ├── config.py           # 환경 설정 관리
│   ├── db/
│   │   ├── __init__.py
│   │   └── connection.py   # ODBC 연결 관리
│   └── tools/
│       ├── __init__.py
│       ├── oee_tools.py    # OEE 관련 툴
│       ├── scrap_tools.py  # Scrap 관련 툴
│       └── margin_tools.py # Margin 관련 툴
├── sql_templates/
│   ├── oee_trend.sql
│   ├── scrap_summary.sql
│   └── margin_by_customer.sql
├── tests/
│   ├── __init__.py
│   ├── test_connection.py
│   └── test_oee_tool.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## SQL 템플릿 수정

SQL 템플릿은 `sql_templates/` 디렉토리에 위치합니다. 실제 QAD/OpenEdge 스키마에 맞게 수정하세요:

1. 테이블/뷰 이름 수정
2. 컬럼 이름 수정
3. 필요한 JOIN 추가
4. 필터 조건 추가

스키마 이름은 `{schema}` placeholder로 지정되어 있으며, `.env`의 `ANALYTICS_SCHEMA` 값으로 치환됩니다.

## 테스트 실행

```bash
pytest tests/ -v
```

## MCP 클라이언트 연결 예시

### Claude Desktop 설정

`claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "openedge-analytics": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/openedge-analytics-mcp"
    }
  }
}
```

## 라이선스

내부 사용 전용

## 문의

QAD/OpenEdge Analytics 관련 문의는 IT 팀에 연락하세요.
