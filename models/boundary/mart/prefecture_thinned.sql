{{ config(materialized='table') }}

SELECT
    LEFT(N03_007, 2) AS prefecture_code,
    N03_001 AS prefecture_name,
    ST_SimplifyPreserveTopology(ST_Union_Agg(ST_MakeValid(geom)), 0.002) AS geometry
FROM {{ ref('stg_prefecture_boundary') }}
WHERE geom IS NOT NULL
GROUP BY LEFT(N03_007, 2), N03_001
