{{ config(tags=['disaster_risk_area']) }}

-- 災害危険区域のポリゴン（オープンデータ公開の地方公共団体が指定した区域のみ）
SELECT
    prefecture_code,
    {{ prefecture_name_from_code('prefecture_code') }} AS prefecture_name,
    municipality_code,
    municipality_name,
    {{ disaster_risk_area_designating_body('designating_body_code') }}
        AS designating_body,
    zone_name,
    address,
    {{ disaster_risk_area_reason('reason_code') }} AS reason,
    reason_detail,
    notice_date,
    notice_number,
    ordinance_name,
    designated_area_ha,
    reference_scale,
    remarks,
    geometry
FROM {{ ref('stg_disaster_risk_area') }}
