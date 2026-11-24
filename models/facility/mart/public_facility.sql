{{ config(materialized='table') }}

-- 市町村役場等及び公的集会施設の位置（ポイント）
WITH municipality AS (
    -- 原典に市区町村名の属性が無いので行政区域から補う。政令市は区まで分かれる
    SELECT DISTINCT
        lg_code,
        city_name,
        ward_name
    FROM {{ ref('stg_administrative_boundary') }}
)

SELECT
    f.admin_code,
    f.prefecture_code,
    f.prefecture_name,
    m.city_name,
    m.ward_name,
    f.facility_class_code,
    f.facility_class,
    f.facility_name,
    f.address,
    f.geometry
FROM {{ ref('stg_public_facility') }} AS f
LEFT JOIN municipality AS m ON f.admin_code = m.lg_code
