{{ config(severity='warn') }}

-- 街区レベルの lg_code は都道府県名・市区町村名の突き合わせで付けるので、
-- 原典の表記が市区町村マスタとずれると NULL になる。ずれた行を市区町村名ごとに挙げる。
-- 市区町村の合併や改称で名前が変わると出るので、出たら突き合わせの規則を見直す
SELECT prefecture_name, city_name, count(*) AS row_count
FROM {{ ref('block') }}
WHERE lg_code IS NULL
GROUP BY prefecture_name, city_name
