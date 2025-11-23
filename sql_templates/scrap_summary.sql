-- =============================================================================
-- Scrap Summary Query Template
-- =============================================================================
-- 목적: 특정 공장의 기간별 Scrap(불량) 요약 조회
--
-- 파라미터:
--   1. plant_id (string): 공장 ID
--   2. from_date (string): 조회 시작일 (YYYY-MM-DD)
--   3. to_date (string): 조회 종료일 (YYYY-MM-DD)
--
-- 동적 치환:
--   - {schema}: 스키마 이름 (config에서 치환)
--   - {group_column}: 그룹화 컬럼 (product_id, workcenter_id, operation_id 중 하나)
--
-- 반환 컬럼:
--   - group_key: 그룹화 기준 값 (제품ID/작업장ID/공정ID)
--   - produced_qty: 총 생산 수량
--   - scrap_qty: 불량 수량
--
-- 참고:
--   - 아래 테이블/컬럼명은 예시입니다. 실제 QAD/OpenEdge 스키마에 맞게 수정하세요.
--   - scrap_rate는 Python 코드에서 계산합니다 (scrap_qty / produced_qty)
-- =============================================================================

SELECT
    {group_column} AS group_key,
    SUM(produced_qty) AS produced_qty,
    SUM(scrap_qty) AS scrap_qty
FROM
    {schema}.production_scrap_detail
WHERE
    plant_id = ?
    AND production_date >= ?
    AND production_date <= ?
GROUP BY
    {group_column}
ORDER BY
    SUM(scrap_qty) DESC

-- =============================================================================
-- 예상 테이블 구조 (참고용):
--
-- CREATE TABLE {schema}.production_scrap_detail (
--     plant_id VARCHAR(20) NOT NULL,        -- 공장 ID (예: PLANT_A)
--     production_date DATE NOT NULL,        -- 생산일자
--     product_id VARCHAR(50) NOT NULL,      -- 제품 ID (예: 2AM051B)
--     workcenter_id VARCHAR(50),            -- 작업장 ID
--     operation_id VARCHAR(50),             -- 공정 ID
--     produced_qty DECIMAL(12,2),           -- 생산 수량
--     scrap_qty DECIMAL(12,2),              -- 불량 수량
--     scrap_reason_code VARCHAR(20),        -- 불량 사유 코드
--     scrap_reason_desc VARCHAR(200),       -- 불량 사유 설명
--     created_at TIMESTAMP,                 -- 생성 일시
--     PRIMARY KEY (plant_id, production_date, product_id, workcenter_id, operation_id)
-- );
--
-- 예상 인덱스:
-- CREATE INDEX idx_scrap_plant_date ON {schema}.production_scrap_detail(plant_id, production_date);
-- CREATE INDEX idx_scrap_product ON {schema}.production_scrap_detail(product_id);
-- CREATE INDEX idx_scrap_workcenter ON {schema}.production_scrap_detail(workcenter_id);
-- =============================================================================
