{{ config(materialized='table') }}

-- 1 行 = 1 人口集中地区。同じ市区町村に複数の地区が設定されることがあるので
-- lg_code は重複する（一意なのは did_code）
SELECT
    did_code,
    lg_code,
    prefecture_code,
    prefecture_name,
    municipality_name,
    did_number,
    population,
    area_km2,
    previous_population,
    previous_area_km2,
    population_share_pct,
    area_share_pct,
    census_year,
    population_male,
    population_female,
    households,
    geometry
FROM {{ ref('stg_did') }}
