{{ config(materialized='table', tags=['medical_area']) }}

-- 二次医療圏の区域ポリゴン（1 行 = 1 医療圏）
SELECT
    area_code,
    area_name,
    prefecture_code,
    prefecture_name,
    planned_area_km2,
    surveyed_area_km2,
    planned_population,
    population,
    population_under_15,
    population_15_to_64,
    population_65_and_over,
    geometry
FROM {{ ref('stg_secondary_medical_area') }}
