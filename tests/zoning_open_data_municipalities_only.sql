-- 用途地域は市区町村ごとに公開条件が異なる。オープンデータ公開可と
-- された市区町村以外が混ざっていないことを確かめる。
SELECT DISTINCT u.admin_code
FROM {{ ref('use_district') }} AS u
LEFT JOIN {{ ref('raw_zoning_license') }} AS l
    ON u.admin_code = l.admin_code
WHERE l.disclosure_category IS DISTINCT FROM 1
