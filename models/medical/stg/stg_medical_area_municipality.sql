{{ config(tags=['medical_area']) }}

SELECT DISTINCT
    admin_code,
    left(admin_code, 2) AS prefecture_code,
    {{ prefecture_name_from_code('left(admin_code, 2)') }} AS prefecture_name,
    municipality_name,
    secondary_area_code,
    secondary_area_name,
    -- 設定フラグ（1=設定あり / 2=設定なし）。一次医療圏を医療計画で定義して
    -- いるかどうかで、区域そのものは定義の有無にかかわらず市区町村と同じ
    primary_area_setting_code = '1' AS primary_area_defined
FROM {{ ref('raw_primary_medical_area') }}
