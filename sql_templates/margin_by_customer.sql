-- =============================================================================
-- Margin by Customer Query Template (QAD OpenEdge)
-- =============================================================================
-- 목적: 특정 기간 동안 고객별 매출/원가/마진 요약 조회
--
-- 데이터 소스:
--   - ih_hist (Invoice Header History) - 송장 헤더
--   - idh_hist (Invoice Detail History) - 송장 상세
--
-- 파라미터:
--   1. period (string): 조회 기간 (YYYY-MM 형식, 예: '2024-01')
--      - 동일 period 값을 2번 바인딩해야 함 (시작일/종료일 계산용)
--   2. customer_id (string, optional): 특정 고객만 조회 시
--
-- 동적 치환:
--   - {schema}: 스키마 이름 (config에서 치환, 기본: PUB)
--   - {customer_filter}: 고객 필터 조건 (Python 코드에서 치환)
--       - customer_id 지정 시: "AND ih.ih_cust = ?"
--       - customer_id 미지정 시: "" (빈 문자열)
--
-- 반환 컬럼:
--   - customer_id: 고객 ID
--   - sales_amount: 총 매출액 (수량 × 단가)
--   - cogs_amount: 총 매출원가 (수량 × 표준원가)
--
-- 참고:
--   - margin_amount와 margin_rate는 Python 코드에서 계산합니다.
--   - QAD ih_hist, idh_hist 테이블 기준으로 작성됨
-- =============================================================================

SELECT
    ih.ih_cust AS customer_id,
    SUM(COALESCE(idh.idh_qty_inv, 0) * COALESCE(idh.idh_price, 0)) AS sales_amount,
    SUM(COALESCE(idh.idh_qty_inv, 0) * COALESCE(idh.idh_std_cost, 0)) AS cogs_amount
FROM
    {schema}.ih_hist ih
    INNER JOIN {schema}.idh_hist idh ON ih.ih_nbr = idh.idh_nbr
WHERE
    -- Period 필터: YYYY-MM 형식으로 월별 조회
    -- ih_inv_date를 YYYY-MM 형식 문자열로 변환하여 비교
    SUBSTRING(CAST(ih.ih_inv_date AS VARCHAR(10)), 1, 7) = ?
    AND ih.ih_invoiced = 1  -- 송장 발행 완료된 건만
    {customer_filter}
GROUP BY
    ih.ih_cust
HAVING
    SUM(COALESCE(idh.idh_qty_inv, 0) * COALESCE(idh.idh_price, 0)) > 0
ORDER BY
    SUM(COALESCE(idh.idh_qty_inv, 0) * COALESCE(idh.idh_price, 0)) DESC

-- =============================================================================
-- 참고: QAD 테이블 구조
--
-- ih_hist (Invoice Header History):
--   - ih_nbr: 송장 번호 (PK)
--   - ih_cust: 고객 코드
--   - ih_inv_date: 송장 발행일
--   - ih_inv_nbr: 세금계산서 번호
--   - ih_invoiced: 송장 발행 여부 (1=발행, 0=미발행)
--   - ih_curr: 통화 코드
--   - ih_ex_rate: 환율
--
-- idh_hist (Invoice Detail History):
--   - idh_nbr: 송장 번호 (FK → ih_hist.ih_nbr)
--   - idh_line: 라인 번호
--   - idh_part: 품목 번호
--   - idh_qty_inv: 송장 수량
--   - idh_price: 단가
--   - idh_std_cost: 표준 원가
--   - idh_prodline: 제품군
--
-- cm_mstr (Customer Master) - 고객명 조회 시 조인:
--   - cm_addr: 고객 코드 (PK)
--   - cm_ship: 고객명
--   - cm_region: 지역
--   - cm_class: 고객 분류
--
-- 확장 쿼리 예시 (고객명 포함):
--   SELECT ih.ih_cust, cm.cm_ship AS customer_name,
--          SUM(idh.idh_qty_inv * idh.idh_price) AS sales
--   FROM {schema}.ih_hist ih
--   JOIN {schema}.idh_hist idh ON ih.ih_nbr = idh.idh_nbr
--   LEFT JOIN {schema}.cm_mstr cm ON ih.ih_cust = cm.cm_addr
--   WHERE SUBSTRING(CAST(ih.ih_inv_date AS VARCHAR(10)), 1, 7) = ?
--   GROUP BY ih.ih_cust, cm.cm_ship
-- =============================================================================
