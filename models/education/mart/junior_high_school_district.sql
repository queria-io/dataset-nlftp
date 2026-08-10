{{ config(materialized='table') }}

-- 中学校の通学区域ポリゴン（利用条件がオープンデータ公開の市区町村のみ）
SELECT
    admin_code,
    prefecture_code,
    prefecture_name,
    municipality_name,
    school_code,
    school_name,
    establisher,
    address,
    geometry
FROM {{ ref('stg_junior_high_school_district') }}
