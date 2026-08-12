-- 土砂災害警戒区域は都道府県ごとに使用許諾条件が異なる。オープンデータとして
-- 利用可とされた都道府県以外が混ざっていないことを確かめる。
SELECT DISTINCT a.prefecture_code
FROM {{ ref('landslide_hazard_area') }} AS a
LEFT JOIN {{ ref('raw_landslide_license') }} AS l
    ON a.prefecture_code = l.prefecture_code
WHERE l.disclosure_category IS DISTINCT FROM 1
