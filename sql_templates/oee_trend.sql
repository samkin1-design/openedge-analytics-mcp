-- =============================================================================
-- OEE Trend Query Template (QAD OpenEdge)
-- =============================================================================
-- 목적: 특정 라인의 기간별 OEE(Overall Equipment Effectiveness) 트렌드 조회
--
-- 데이터 소스: op_hist (Operation History)
--
-- OEE 계산 방식:
--   - Availability (가용성) = 실제 가동시간 / 표준(계획) 가동시간
--   - Performance (성능)   = 실제 생산량 / 이론적 생산량
--   - Quality (품질)       = 양품수량 / 총생산수량
--   - OEE = Availability × Performance × Quality
--
-- 파라미터:
--   1. line_id (string): 생산 라인 ID (op_line 값)
--   2. from_date (string): 조회 시작일 (YYYY-MM-DD)
--   3. to_date (string): 조회 종료일 (YYYY-MM-DD)
--
-- 반환 컬럼:
--   - production_date: 생산일자
--   - oee: OEE 지표 (0.0 ~ 1.0)
--   - availability: 가용성 (0.0 ~ 1.0)
--   - performance: 성능 (0.0 ~ 1.0)
--   - quality: 품질 (0.0 ~ 1.0)
--
-- 참고:
--   - {schema}는 런타임에 config.analytics_schema 값으로 치환됩니다 (기본: PUB)
--   - QAD op_hist 테이블 기준으로 작성됨
-- =============================================================================

SELECT
    op_date AS production_date,
    -- OEE = Availability × Performance × Quality
    CASE
        WHEN SUM(op_std_run) > 0
             AND SUM(op_act_run) > 0
             AND SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)) > 0
        THEN
            -- Availability × Performance × Quality 계산
            CAST(
                (CAST(SUM(op_act_run) AS FLOAT) / NULLIF(SUM(op_std_run), 0)) *
                (CAST(SUM(COALESCE(op_qty_comp, 0)) AS FLOAT) /
                 NULLIF(SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)), 0)) *
                (CAST(SUM(COALESCE(op_qty_comp, 0)) AS FLOAT) /
                 NULLIF(SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)), 0))
            AS FLOAT)
        ELSE 0
    END AS oee,
    -- Availability: 실제가동시간 / 표준(계획)시간
    CASE
        WHEN SUM(op_std_run) > 0
        THEN CAST(SUM(op_act_run) AS FLOAT) / SUM(op_std_run)
        ELSE 0
    END AS availability,
    -- Performance: 실제 생산성 (여기서는 1.0으로 가정, 실제 환경에 맞게 조정)
    CASE
        WHEN SUM(op_std_run) > 0
        THEN CAST(SUM(op_act_run) AS FLOAT) / SUM(op_std_run)
        ELSE 0
    END AS performance,
    -- Quality: 양품수량 / 총생산수량
    CASE
        WHEN SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)) > 0
        THEN CAST(SUM(COALESCE(op_qty_comp, 0)) AS FLOAT) /
             SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0))
        ELSE 0
    END AS quality
FROM
    {schema}.op_hist
WHERE
    op_line = ?
    AND op_date >= ?
    AND op_date <= ?
GROUP BY
    op_date
ORDER BY
    op_date ASC

-- =============================================================================
-- 참고: QAD op_hist 주요 컬럼
--
-- op_hist 테이블 (Operation History):
--   - op_line: 생산 라인 ID
--   - op_date: 작업 일자
--   - op_wkctr: 작업장 (Work Center)
--   - op_wo_nbr: 작업지시 번호
--   - op_act_run: 실제 가동 시간 (분)
--   - op_std_run: 표준 가동 시간 (분)
--   - op_act_setup: 실제 셋업 시간
--   - op_std_setup: 표준 셋업 시간
--   - op_qty_comp: 완료(양품) 수량
--   - op_qty_rjct: 불합격 수량
--   - op_qty_scrap: 스크랩 수량
--   - op_type: 트랜잭션 유형
--   - op_site: 사이트/공장
--   - op_part: 품목 번호
--
-- 주의사항:
--   1. OEE 계산 방식은 회사 정의에 따라 다를 수 있음
--   2. Performance 계산은 이상 사이클타임 데이터가 필요하며, 현재는 간소화됨
--   3. 시간 단위(분/시간)는 환경에 맞게 변환 필요
-- =============================================================================
