{{ config(tags=['landslide_prevention']) }}

-- 地すべり防止区域のポリゴン（オープンデータ公開の都道府県 × 所管省庁のみ）
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
    {{ landslide_prevention_agency_name('competent_agency_code') }}
        AS competent_agency,
    geometry
FROM {{ ref('stg_landslide_prevention_zone') }}
