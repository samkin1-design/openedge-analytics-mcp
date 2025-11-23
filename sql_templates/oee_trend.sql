SELECT
    op_date AS production_date,
    CASE
        WHEN SUM(op_std_run) > 0
             AND SUM(op_act_run) > 0
             AND SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)) > 0
        THEN
            CAST(
                (CAST(SUM(op_act_run) AS FLOAT) / NULLIF(SUM(op_std_run), 0)) *
                (CAST(SUM(COALESCE(op_qty_comp, 0)) AS FLOAT) /
                 NULLIF(SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)), 0)) *
                (CAST(SUM(COALESCE(op_qty_comp, 0)) AS FLOAT) /
                 NULLIF(SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)), 0))
            AS FLOAT)
        ELSE 0
    END AS oee,
    CASE
        WHEN SUM(op_std_run) > 0
        THEN CAST(SUM(op_act_run) AS FLOAT) / SUM(op_std_run)
        ELSE 0
    END AS availability,
    CASE
        WHEN SUM(op_std_run) > 0
        THEN CAST(SUM(op_act_run) AS FLOAT) / SUM(op_std_run)
        ELSE 0
    END AS performance,
    CASE
        WHEN SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0)) > 0
        THEN CAST(SUM(COALESCE(op_qty_comp, 0)) AS FLOAT) /
             SUM(COALESCE(op_qty_comp, 0) + COALESCE(op_qty_scrap, 0) + COALESCE(op_qty_rjct, 0))
        ELSE 0
    END AS quality
FROM
    {schema}.op_hist
WHERE
    op_wkctr = '{wkctr}'
    AND op_date >= '{from_date}'
    AND op_date <= '{to_date}'
GROUP BY
    op_date
ORDER BY
    op_date ASC
