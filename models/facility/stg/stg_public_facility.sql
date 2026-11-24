SELECT
    f.P05_001 AS admin_code,
    LEFT(f.P05_001, 2) AS prefecture_code,
    {{ prefecture_name_from_code('LEFT(f.P05_001, 2)') }} AS prefecture_name,
    f.P05_002 AS facility_class_code,
    {{ public_facility_class_name('f.P05_002') }} AS facility_class,
    f.P05_003 AS facility_name,
    f.P05_004 AS address,
    ST_MakeValid(f.geom) AS geometry
FROM {{ ref('raw_public_facility') }} AS f
WHERE f.geom IS NOT NULL
