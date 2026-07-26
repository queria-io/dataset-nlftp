-- 用途地域のポリゴン（オープンデータ公開可の市区町村のみ）
SELECT
    admin_code,
    prefecture_code,
    prefecture_name,
    municipality_name,
    zoning_code,
    zoning_name,
    building_coverage_ratio,
    floor_area_ratio,
    geometry
FROM {{ ref('stg_zoning') }}
