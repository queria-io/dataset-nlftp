{{ config(tags=['sabo']) }}

-- 砂防指定地のポリゴン（原典資料の提供があった都道府県のみ）
SELECT
    area.prefecture_code,
    {{ prefecture_name_from_code('area.prefecture_code') }} AS prefecture_name,
    area.municipality_code,
    area.municipality_name,
    area.river_name,
    area.tributary_name,
    area.notice_date,
    area.notice_date_text,
    area.notice_number,
    area.designated_area_ha,
    area.reference_number,
    area.designation_method,
    datapoint.as_of AS data_as_of,
    area.geometry
FROM {{ ref('stg_sabo_designated_area') }} AS area
LEFT JOIN {{ ref('raw_sabo_datapoint') }} AS datapoint
    ON area.prefecture_code = datapoint.prefecture_code
