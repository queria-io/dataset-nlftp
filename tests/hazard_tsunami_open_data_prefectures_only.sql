-- 津波浸水想定は都道府県ごとに使用許諾条件が異なる。オープンデータとして
-- 利用可とされた都道府県以外が混ざっていないことを確かめる。
SELECT DISTINCT t.prefecture_code
FROM {{ ref('tsunami_inundation') }} AS t
LEFT JOIN {{ ref('raw_tsunami_license') }} AS l
    ON t.prefecture_code = l.prefecture_code
WHERE l.disclosure_category IS DISTINCT FROM 1
