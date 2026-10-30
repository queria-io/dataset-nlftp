{{ config(materialized='table', tags=['isj']) }}

-- 原典の市区町村コードは 5 桁なので、ABR の市区町村マスタで 6 桁の lg_code にする
WITH cities AS (
    SELECT lg_code, LEFT(lg_code, 5) AS city_code
    FROM {{ ref('raw_mt_city') }}
    WHERE ablt_date IS NULL
)
SELECT
    c.lg_code,
    o.prefecture_code,
    o.prefecture_name,
    o.city_name,
    o.oaza_chome_code,
    o.oaza_chome_name,
    o.oaza_chome_class_code,
    o.source_material_code,
    o.lat,
    o.lng,
    ST_Point(o.lng, o.lat) AS geometry
FROM {{ ref('stg_oaza') }} o
LEFT JOIN cities c ON c.city_code = o.city_code
ORDER BY c.lg_code, o.oaza_chome_code
