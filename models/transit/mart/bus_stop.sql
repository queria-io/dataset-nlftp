{{ config(materialized='table') }}

-- バス停留所の位置（ポイント）
SELECT
    prefecture_code,
    stop_name,
    operator,
    bus_class_codes,
    bus_classes,
    route_count,
    routes,
    remarks,
    geometry
FROM {{ ref('stg_bus_stop') }}
