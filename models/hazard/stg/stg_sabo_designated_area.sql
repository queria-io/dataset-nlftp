{{ config(tags=['sabo']) }}

SELECT
    prefecture_code,
    NULLIF(TRIM(municipality_code), '') AS municipality_code,
    NULLIF(TRIM(municipality_name), '') AS municipality_name,
    NULLIF(TRIM(river_name), '') AS river_name,
    NULLIF(TRIM(tributary_name), '') AS tributary_name,
    NULLIF(TRIM(notice_date_text), '') AS notice_date_text,
    -- 告示年月日は表記がそろっていないので、和暦の年月日として読めるものだけを
    -- 日付にする
    {{ sabo_notice_date('notice_date_text') }} AS notice_date,
    NULLIF(TRIM(notice_number), '') AS notice_number,
    -- 指定面積の未記載は 0 で入っている（面積 0 の指定地は存在しない）
    NULLIF(designated_area_ha, 0) AS designated_area_ha,
    NULLIF(TRIM(reference_number), '') AS reference_number,
    NULLIF(TRIM(designation_method), '') AS designation_method,
    -- 自己交差のあるポリゴンを ST_MakeValid で直すと GEOMETRYCOLLECTION になる
    -- ことがある（面だけが入っていて面積は変わらない）。面として扱えるように
    -- 面の要素だけを取り出す
    CASE
        WHEN ST_GeometryType(ST_MakeValid(ST_GeomFromWKB(geom)))
            = 'GEOMETRYCOLLECTION'
        THEN ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(geom)), 3)
        ELSE ST_MakeValid(ST_GeomFromWKB(geom))
    END AS geometry
FROM {{ ref('raw_sabo_designated_area') }}
WHERE geom IS NOT NULL
