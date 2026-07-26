SELECT
    admin_code,
    left(admin_code, 2) AS prefecture_code,
    {{ prefecture_name_from_code('left(admin_code, 2)') }} AS prefecture_name,
    municipality_name,
    zoning_code,
    {{ use_district_name('zoning_code') }} AS zoning_name,
    -- 建ぺい率・容積率は原典で不明のとき 9999。指定値としてありえない 0 も
    -- 同じく不明として扱う
    NULLIF(NULLIF(building_coverage_ratio, 9999), 0) AS building_coverage_ratio,
    NULLIF(NULLIF(floor_area_ratio, 9999), 0) AS floor_area_ratio,
    ST_MakeValid(ST_GeomFromWKB(geom)) AS geometry
FROM {{ ref('raw_zoning') }}
WHERE geom IS NOT NULL
