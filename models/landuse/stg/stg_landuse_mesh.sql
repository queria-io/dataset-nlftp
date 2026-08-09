-- 都市地域土地利用細分メッシュのステージング。
--
-- 細分メッシュコードは 3 次メッシュコード 8 桁 + 1/10 細分の行列 2 桁で、
-- 先頭 8 桁がそのまま 1km メッシュのコードになる。
-- ジオメトリは 100m 四方の矩形で不正なものが無いため ST_MakeValid は掛けない。
SELECT
    mesh_code,
    substr(mesh_code, 1, 8) AS mesh_1km_code,
    landuse_code,
    {{ landuse_name('landuse_code') }} AS landuse,
    try_strptime(survey_date, '%Y%m%d')::DATE AS survey_date,
    ST_GeomFromWKB(geom) AS geometry
FROM {{ ref('raw_landuse_mesh') }}
WHERE geom IS NOT NULL
