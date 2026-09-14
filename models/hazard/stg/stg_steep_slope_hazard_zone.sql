{{ config(tags=['steep_slope']) }}

SELECT
    prefecture_code,
    NULLIF(municipality_code, '') AS municipality_code,
    NULLIF(municipality_name, '') AS municipality_name,
    NULLIF(zone_name, '') AS zone_name,
    NULLIF(address, '') AS address,
    -- 公示年月日の不明は 9999/1/1 で入っているので日付には残さない
    CASE
        WHEN notice_date = '9999/1/1' THEN NULL
        ELSE CAST(STRPTIME(notice_date, '%Y/%-m/%-d') AS DATE)
    END AS notice_date,
    NULLIF(notice_number, '') AS notice_number,
    -- 指定面積の未記載は 0 で入っている（面積 0 の区域は存在しない）
    NULLIF(designated_area_ha, 0) AS designated_area_ha,
    -- 自己交差のあるポリゴンを ST_MakeValid で直すと GEOMETRYCOLLECTION になる
    -- ことがある（面だけが入っていて面積は変わらない）。面として扱えるように
    -- 面の要素だけを取り出す
    CASE
        WHEN ST_GeometryType(ST_MakeValid(ST_GeomFromWKB(geom)))
            = 'GEOMETRYCOLLECTION'
        THEN ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(geom)), 3)
        ELSE ST_MakeValid(ST_GeomFromWKB(geom))
    END AS geometry
FROM {{ ref('raw_steep_slope_hazard_zone') }}
WHERE geom IS NOT NULL
