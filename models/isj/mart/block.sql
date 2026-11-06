{{ config(materialized='table', tags=['isj']) }}

-- 原典に市区町村コードが無いので、都道府県名・市区町村名で突き合わせて lg_code を付ける
-- （規則は macros/isj.sql の isj_city_names）
WITH cities AS (
{{ isj_city_names() }}
)
SELECT
    c.lg_code,
    b.prefecture_name,
    b.city_name,
    b.oaza_chome_name,
    b.koaza_name,
    b.block_number,
    b.plane_rectangular_zone,
    b.x,
    b.y,
    b.lat,
    b.lng,
    b.is_residential_address,
    b.is_representative,
    b.before_update_flag,
    b.after_update_flag,
    ST_Point(b.lng, b.lat) AS geometry
FROM {{ ref('stg_block') }} b
LEFT JOIN cities c ON c.pref = b.prefecture_name AND c.name = b.city_name
-- 履歴フラグの 3 は削除された街区符号・地番。原典の利用上の注意に従って除く
WHERE b.before_update_flag IS DISTINCT FROM '3'
    AND b.after_update_flag IS DISTINCT FROM '3'
ORDER BY c.lg_code, b.oaza_chome_name, b.koaza_name, b.block_number
