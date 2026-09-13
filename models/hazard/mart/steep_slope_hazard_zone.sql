{{ config(tags=['steep_slope']) }}

-- 急傾斜地崩壊危険区域のポリゴン（オープンデータ公開の都道府県のみ）
SELECT
    prefecture_code,
    {{ prefecture_name_from_code('prefecture_code') }} AS prefecture_name,
    municipality_code,
    municipality_name,
    zone_name,
    address,
    notice_date,
    notice_number,
    designated_area_ha,
    geometry
FROM {{ ref('stg_steep_slope_hazard_zone') }}
