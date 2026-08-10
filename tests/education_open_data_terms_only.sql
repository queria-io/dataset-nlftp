-- 通学区域は市区町村ごとに利用条件が異なる。利用条件がオープンデータ公開と
-- された市区町村以外が混ざっていないことを、小学校区・中学校区それぞれで確かめる。
SELECT 'elementary' AS district, d.admin_code
FROM {{ ref('elementary_school_district') }} AS d
LEFT JOIN {{ ref('raw_school_district_terms') }} AS t
    ON d.admin_code = t.admin_code
WHERE t.elementary_terms IS DISTINCT FROM 'オープンデータ公開'

UNION ALL

SELECT 'junior_high' AS district, d.admin_code
FROM {{ ref('junior_high_school_district') }} AS d
LEFT JOIN {{ ref('raw_school_district_terms') }} AS t
    ON d.admin_code = t.admin_code
WHERE t.junior_high_terms IS DISTINCT FROM 'オープンデータ公開'
