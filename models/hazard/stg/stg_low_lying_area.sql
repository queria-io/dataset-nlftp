{{ config(tags=['lowland']) }}

SELECT
    prefecture_code,
    area_ha,
    max_inundation_depth_m,
    TRIM(reference_data_code) AS reference_data_code,
    -- 自己交差のあるポリゴンを ST_MakeValid で直すと GEOMETRYCOLLECTION になる
    -- ことがある（面だけが入っていて面積は変わらない）。面として扱えるように
    -- 面の要素だけを取り出す
    CASE
        WHEN ST_GeometryType(ST_MakeValid(ST_GeomFromWKB(geom)))
            = 'GEOMETRYCOLLECTION'
        THEN ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(geom)), 3)
        ELSE ST_MakeValid(ST_GeomFromWKB(geom))
    END AS geometry
FROM {{ ref('raw_low_lying_area') }}
WHERE geom IS NOT NULL
