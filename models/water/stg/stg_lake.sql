{{ config(tags=['lake']) }}

SELECT
    record_number,
    TRIM(lake_name) AS lake_name,
    -- 行政区域コードはカンマ区切りで、末尾にカンマが付く行がある
    list_filter(string_split(lg_codes, ','), x -> x <> '') AS lg_codes,
    -- 最大水深は「日本の湖沼アトラス」に載る自然湖沼にだけ値がある。
    -- それ以外の湖沼にも 0 が入る行があり、水深 0m の湖沼は無いので未記載とみなす
    NULLIF(TRY_CAST(NULLIF(TRIM(max_depth_m), '') AS INTEGER), 0) AS max_depth_m,
    TRY_CAST(NULLIF(TRIM(water_surface_elevation_m), '') AS INTEGER)
        AS water_surface_elevation_m,
    ST_GeomFromWKB(geom) AS geometry
FROM {{ ref('raw_lake') }}
WHERE geom IS NOT NULL
