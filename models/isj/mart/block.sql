{{ config(materialized='table', tags=['isj']) }}

-- 原典に市区町村コードが無いので、ABR の市区町村マスタと都道府県名・市区町村名で
-- 突き合わせて 6 桁の lg_code を付ける。原典の市区町村名は郡名を含む町村
-- （西多摩郡瑞穂町）と含まない町村があり、政令市は市名と区名を続けて書く
WITH cities AS (
    SELECT lg_code, pref, coalesce(county, '') || city || coalesce(ward, '') AS name
    FROM {{ ref('raw_mt_city') }}
    WHERE ablt_date IS NULL AND city IS NOT NULL
    UNION
    SELECT lg_code, pref, city || coalesce(ward, '') AS name
    FROM {{ ref('raw_mt_city') }}
    WHERE ablt_date IS NULL AND city IS NOT NULL
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
ORDER BY c.lg_code, b.oaza_chome_name, b.koaza_name, b.block_number
