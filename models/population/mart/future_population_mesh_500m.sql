{{ config(materialized='table') }}

-- 500mメッシュ単位の将来推計人口。1kmメッシュでは粗すぎる商圏分析や按分の用途向け。
-- city_code は複数市区町村にまたがるメッシュでは "_" 連結となる。
SELECT
    mesh_id,
    city_code,
    population_2025,
    population_2035,
    population_2050,
    ROUND(
        100.0 * (population_2050 - population_2025)
        / NULLIF(population_2025, 0),
        1
    ) AS growth_rate_2025_2050,
    ROUND(100.0 * elderly_2025 / NULLIF(population_2025, 0), 1) AS elderly_ratio_2025,
    ROUND(100.0 * elderly_2050 / NULLIF(population_2050, 0), 1) AS elderly_ratio_2050,
    geometry
FROM {{ ref('stg_future_population_mesh_500m') }}
