{{ config(materialized='table') }}

-- バス路線の経路（ライン）。原典は経路を細かい区間に分けて持つため 1 行 = 1 区間。
SELECT
    operator,
    geometry
FROM {{ ref('stg_bus_route') }}
