-- 急傾斜地崩壊危険区域は都道府県ごとに公開条件が異なる。「オープンデータにて公開」
-- とされた都道府県以外が混ざっていないことを確かめる。
SELECT DISTINCT z.prefecture_code
FROM {{ ref('steep_slope_hazard_zone') }} AS z
LEFT JOIN {{ ref('raw_steep_slope_terms') }} AS t
    ON z.prefecture_code = t.prefecture_code
WHERE t.disclosure IS DISTINCT FROM 'オープンデータにて公開'
