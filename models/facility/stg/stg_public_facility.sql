WITH municipality AS (
    -- 原典に市区町村名の属性が無いので行政区域から補う。政令市は区まで分かれる
    SELECT DISTINCT
        lg_code,
        city_name,
        ward_name
    FROM {{ ref('stg_administrative_boundary') }}
)

SELECT
    f.P05_001 AS admin_code,
    LEFT(f.P05_001, 2) AS prefecture_code,
    {{ prefecture_name_from_code('LEFT(f.P05_001, 2)') }} AS prefecture_name,
    m.city_name,
    m.ward_name,
    f.P05_002 AS facility_class_code,
    {{ public_facility_class_name('f.P05_002') }} AS facility_class,
    f.P05_003 AS facility_name,
    f.P05_004 AS address,
    ST_MakeValid(f.geom) AS geometry
FROM {{ ref('raw_public_facility') }} AS f
LEFT JOIN municipality AS m ON f.P05_001 = m.lg_code
WHERE f.geom IS NOT NULL
