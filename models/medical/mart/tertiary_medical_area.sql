{{ config(materialized='table', tags=['medical_area']) }}

-- 三次医療圏の区域ポリゴン（1 行 = 1 医療圏）
SELECT
    prefecture_code,
    prefecture_name,
    area_name,
    geometry
FROM {{ ref('stg_tertiary_medical_area') }}
