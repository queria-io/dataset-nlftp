{{ config(tags=['large_fill']) }}

SELECT
    prefecture_code,
    municipality_code,
    municipality_name,
    fill_type_code,
    -- 豊田市は全行の盛土番号が '-' で、番号を持たない
    NULLIF(fill_number, '-') AS fill_number,
    -- 自己交差のあるポリゴンを ST_MakeValid で直すと GEOMETRYCOLLECTION になる
    -- ことがある。面として扱えるように面の要素だけを取り出す
    CASE
        WHEN ST_GeometryType(ST_MakeValid(ST_GeomFromWKB(geom)))
            = 'GEOMETRYCOLLECTION'
        THEN ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(geom)), 3)
        ELSE ST_MakeValid(ST_GeomFromWKB(geom))
    END AS geometry
FROM {{ ref('raw_large_fill_area') }}
WHERE geom IS NOT NULL
