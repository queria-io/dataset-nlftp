{{ config(tags=['landslide']) }}

-- 土砂災害警戒区域・特別警戒区域のポリゴン（オープンデータ利用可の都道府県のみ）
SELECT
    prefecture_code,
    {{ prefecture_name_from_code('prefecture_code') }} AS prefecture_name,
    phenomenon_code,
    {{ landslide_phenomenon_name('phenomenon_code') }} AS phenomenon,
    zone_code,
    {{ landslide_zone_type('zone_code') }} AS zone_type,
    {{ landslide_is_designated('zone_code') }} AS is_designated,
    zone_number,
    zone_name,
    address,
    notice_date,
    special_zone_unspecified,
    geometry
FROM {{ ref('stg_landslide_hazard_area') }}
