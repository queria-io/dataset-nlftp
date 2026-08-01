-- 100m メッシュ単位の土地利用（ポリゴン）
SELECT
    mesh_code,
    mesh_1km_code,
    landuse_code,
    landuse,
    survey_date,
    geometry
FROM {{ ref('stg_landuse_mesh') }}
