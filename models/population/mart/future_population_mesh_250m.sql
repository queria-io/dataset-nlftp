{{ config(materialized='table') }}

-- 250mメッシュ単位の将来推計人口。駅前や商店街など、500mメッシュでも粗い範囲の人口を見る用途向け。
-- 250mメッシュは1つの市区町村に割り当てられていて、city_code は "_" 連結にならない。
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
FROM {{ ref('stg_future_population_mesh_250m') }}
