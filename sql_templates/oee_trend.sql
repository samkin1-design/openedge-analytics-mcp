-- =============================================================================
-- OEE Trend Query Template
-- =============================================================================
-- 목적: 특정 라인의 기간별 OEE(Overall Equipment Effectiveness) 트렌드 조회
--
-- 파라미터:
--   1. line_id (string): 생산 라인 ID
--   2. from_date (string): 조회 시작일 (YYYY-MM-DD)
--   3. to_date (string): 조회 종료일 (YYYY-MM-DD)
--
-- 반환 컬럼:
--   - production_date: 생산일자 (YYYY-MM-DD)
--   - oee: OEE 지표 (0.0 ~ 1.0)
--   - availability: 가용성 (0.0 ~ 1.0)
--   - performance: 성능 (0.0 ~ 1.0)
--   - quality: 품질 (0.0 ~ 1.0)
--
-- 참고:
--   - {schema}는 런타임에 config.analytics_schema 값으로 치환됩니다.
--   - 아래 테이블/컬럼명은 예시입니다. 실제 QAD/OpenEdge 스키마에 맞게 수정하세요.
-- =============================================================================

SELECT
    production_date,
    oee,
    availability,
    performance,
    quality
FROM
    {schema}.oee_daily_metrics
WHERE
    line_id = ?
    AND production_date >= ?
    AND production_date <= ?
ORDER BY
    production_date ASC

-- =============================================================================
-- 예상 테이블 구조 (참고용):
--
-- CREATE TABLE {schema}.oee_daily_metrics (
--     line_id VARCHAR(50) NOT NULL,          -- 생산 라인 ID (예: LINE_01)
--     production_date DATE NOT NULL,         -- 생산일자
--     planned_production_time DECIMAL(10,2), -- 계획 생산 시간 (분)
--     actual_run_time DECIMAL(10,2),         -- 실제 가동 시간 (분)
--     ideal_cycle_time DECIMAL(10,4),        -- 이상적 사이클 타임 (분/개)
--     total_count INTEGER,                   -- 총 생산 수량
--     good_count INTEGER,                    -- 양품 수량
--     availability DECIMAL(5,4),             -- 가용성 = 실제가동시간 / 계획생산시간
--     performance DECIMAL(5,4),              -- 성능 = (총생산수량 * 이상사이클타임) / 실제가동시간
--     quality DECIMAL(5,4),                  -- 품질 = 양품수량 / 총생산수량
--     oee DECIMAL(5,4),                      -- OEE = 가용성 * 성능 * 품질
--     PRIMARY KEY (line_id, production_date)
-- );
-- =============================================================================
