{{ config(materialized='table', tags=['medical_area']) }}

-- 市区町村と二次医療圏の対応表（1 行 = 1 市区町村）
SELECT
    admin_code,
    municipality_name,
    prefecture_code,
    prefecture_name,
    secondary_area_code,
    secondary_area_name,
    primary_area_defined
FROM {{ ref('stg_medical_area_municipality') }}
