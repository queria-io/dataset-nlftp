{{ config(
    tags=['flood'],
    pre_hook="CALL nlftp.set_option('parquet_row_group_size', 12288, schema => 'hazard')",
    post_hook="CALL nlftp.set_option('parquet_row_group_size', 122880, schema => 'hazard')",
) }}

-- 地点を含む区画を探すとき、xmin・ymin・xmax・ymax の条件で行グループを飛ばせるようにする。
-- 行を位置の順 (ST_Hilbert) に並べ、行グループを 12,288 行にする。
-- 行グループの大きさは DuckDB が並列に書く単位 (122,880 行) を割り切り、2,048 行の倍数にする。
-- 割り切れないと単位の端の行が別の単位の行と 1 つの行グループにまとまり、並びが崩れる。
-- 設定はスキーマに付く (dbt は __dbt_tmp に書いてから改名するので、テーブルに付けても効かない) ため、
-- 書き終えたら hazard の既定の 122,880 行に戻す
WITH fixed AS (
    SELECT
        region_code,
        river_code,
        river_name,
        admin_code,
        admin_name,
        depth_rank,
        ST_MakeValid(ST_GeomFromWKB(geom)) AS geometry
    FROM {{ ref('raw_flood_inundation') }}
    WHERE geom IS NOT NULL
)

SELECT
    * EXCLUDE (geometry),
    ST_XMin(geometry) AS xmin,
    ST_YMin(geometry) AS ymin,
    ST_XMax(geometry) AS xmax,
    ST_YMax(geometry) AS ymax,
    geometry
FROM fixed
-- ST_Hilbert は空のジオメトリでエラーになるので、空の行は位置を持たない行として末尾に置く
ORDER BY CASE
    WHEN NOT ST_IsEmpty(geometry)
        THEN ST_Hilbert(geometry, {'min_x': 122.0, 'min_y': 20.0, 'max_x': 154.0, 'max_y': 46.0}::BOX_2D)
END
