{{ config(tags=['lowland']) }}

-- 低位地帯（標高メッシュから抽出した 1ha 以上の凹地）のポリゴン
SELECT
    prefecture_code,
    {{ prefecture_name_from_code('prefecture_code') }} AS prefecture_name,
    area_ha,
    max_inundation_depth_m,
    reference_data_code,
    {{ lowland_reference_data_name('reference_data_code') }} AS reference_data,
    geometry
FROM {{ ref('stg_low_lying_area') }}
