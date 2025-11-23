-- =============================================================================
-- Margin by Customer Query Template
-- =============================================================================
-- 목적: 특정 기간 동안 고객별 매출/원가/마진 요약 조회
--
-- 파라미터:
--   1. period (string): 조회 기간 ('YYYY-MM', 'YYYYQN', 'YYYY' 형식)
--   2. customer_id (string, optional): 고객 ID (특정 고객만 조회 시)
--
-- 동적 치환:
--   - {schema}: 스키마 이름 (config에서 치환)
--   - {customer_filter}: 고객 필터 조건 (Python 코드에서 치환)
--       - customer_id 지정 시: "AND customer_id = ?"
--       - customer_id 미지정 시: "" (빈 문자열)
--
-- 반환 컬럼:
--   - customer_id: 고객 ID
--   - sales_amount: 총 매출액
--   - cogs_amount: 총 매출원가 (Cost of Goods Sold)
--
-- 참고:
--   - margin_amount와 margin_rate는 Python 코드에서 계산합니다.
--   - 아래 테이블/컬럼명은 예시입니다. 실제 QAD/OpenEdge 스키마에 맞게 수정하세요.
-- =============================================================================

SELECT
    customer_id,
    SUM(sales_amount) AS sales_amount,
    SUM(cogs_amount) AS cogs_amount
FROM
    {schema}.customer_margin_summary
WHERE
    fiscal_period = ?
    {customer_filter}
GROUP BY
    customer_id
ORDER BY
    SUM(sales_amount) DESC

-- =============================================================================
-- 예상 테이블 구조 (참고용):
--
-- CREATE TABLE {schema}.customer_margin_summary (
--     fiscal_period VARCHAR(10) NOT NULL,   -- 회계 기간 (예: '2024-01', '2024Q1', '2024')
--     customer_id VARCHAR(50) NOT NULL,     -- 고객 ID (예: 'BMW', 'HYUNDAI')
--     customer_name VARCHAR(200),           -- 고객명
--     sales_amount DECIMAL(18,2),           -- 매출액
--     cogs_amount DECIMAL(18,2),            -- 매출원가 (Cost of Goods Sold)
--     gross_margin DECIMAL(18,2),           -- 매출총이익 = 매출액 - 매출원가
--     gross_margin_rate DECIMAL(8,4),       -- 매출총이익률 = 매출총이익 / 매출액
--     order_count INTEGER,                  -- 주문 건수
--     ship_count INTEGER,                   -- 출하 건수
--     created_at TIMESTAMP,                 -- 생성 일시
--     updated_at TIMESTAMP,                 -- 수정 일시
--     PRIMARY KEY (fiscal_period, customer_id)
-- );
--
-- 예상 인덱스:
-- CREATE INDEX idx_margin_period ON {schema}.customer_margin_summary(fiscal_period);
-- CREATE INDEX idx_margin_customer ON {schema}.customer_margin_summary(customer_id);
--
-- 참고: fiscal_period 형식 예시
--   - 월별: '2024-01', '2024-02', ..., '2024-12'
--   - 분기별: '2024Q1', '2024Q2', '2024Q3', '2024Q4'
--   - 연간: '2024', '2025'
-- =============================================================================
