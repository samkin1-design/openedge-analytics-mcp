-- =============================================================================
-- Scrap Summary Query Template (QAD OpenEdge)
-- =============================================================================
-- 목적: 특정 공장의 기간별 Scrap(불량) 요약 조회
--
-- 데이터 소스: op_hist (Operation History)
--
-- 파라미터:
--   1. plant_id (string): 공장/사이트 ID (op_site 값)
--   2. from_date (string): 조회 시작일 (YYYY-MM-DD)
--   3. to_date (string): 조회 종료일 (YYYY-MM-DD)
--
-- 동적 치환:
--   - {schema}: 스키마 이름 (config에서 치환, 기본: PUB)
--   - {group_column}: 그룹화 컬럼 (op_part, op_wkctr, op_wo_op 중 하나)
--
-- 반환 컬럼:
--   - group_key: 그룹화 기준 값 (제품ID/작업장ID/공정ID)
--   - produced_qty: 총 생산 수량 (양품 + 불량 + 스크랩)
--   - scrap_qty: 스크랩 수량
--
-- 참고:
--   - scrap_rate는 Python 코드에서 계산합니다 (scrap_qty / produced_qty)
--   - QAD op_hist 테이블 기준으로 작성됨
-- =============================================================================

SELECT
    {group_column} AS group_key,
    SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)) AS produced_qty,
    SUM(COALESCE(op_qty_scrap, 0)) AS scrap_qty
FROM
    {schema}.op_hist
WHERE
    op_site = ?
    AND op_date >= ?
    AND op_date <= ?
GROUP BY
    {group_column}
HAVING
    SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)) > 0
ORDER BY
    SUM(COALESCE(op_qty_scrap, 0)) DESC

-- =============================================================================
-- group_column 매핑 (Python scrap_tools.py에서 설정):
--
--   group_by='product'    → group_column='op_part'     (품목별)
--   group_by='workcenter' → group_column='op_wkctr'    (작업장별)
--   group_by='operation'  → group_column='op_wo_op'    (공정별)
--
-- =============================================================================
-- 참고: QAD op_hist 주요 컬럼 (Scrap 관련)
--
--   - op_site: 사이트/공장 ID
--   - op_part: 품목 번호
--   - op_wkctr: 작업장 ID (Work Center)
--   - op_wo_op: 작업지시 공정 번호
--   - op_date: 작업 일자
--   - op_qty_comp: 완료(양품) 수량
--   - op_qty_rjct: 불합격 수량
--   - op_qty_scrap: 스크랩 수량
--   - op_rsn_scrap: 스크랩 사유 코드
--   - op_wo_nbr: 작업지시 번호
--
-- 확장 쿼리 예시 (스크랩 사유별 분석):
--   SELECT op_rsn_scrap AS reason_code, SUM(op_qty_scrap) AS scrap_qty
--   FROM {schema}.op_hist
--   WHERE op_site = ? AND op_date BETWEEN ? AND ?
--   GROUP BY op_rsn_scrap
--   ORDER BY scrap_qty DESC
-- =============================================================================
