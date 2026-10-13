-- 行政区域コードは .dbf の文字列をカンマで分けて作る。デコードの桁ずれや
-- 区切りの変化で 5 桁の数字にならない要素が混ざると、市区町村との結合が
-- 黙って外れるので検査する。
SELECT record_number, lake_name, lg_codes
FROM {{ ref('lake') }}
WHERE len(lg_codes) = 0
   OR len(list_filter(lg_codes, x -> NOT regexp_full_match(x, '[0-9]{5}'))) > 0
