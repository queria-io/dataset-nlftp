-- 500mメッシュは1kmメッシュと同じ推計を細かい粒度で集計し直したもので、
-- メッシュコードの先頭8桁が1kmメッシュのコードになる。粒度をまたいだ結合は
-- この桁で行うため、対応が崩れていないことを検査する。
SELECT DISTINCT substr(mesh_id, 1, 8) AS mesh_1km_code
FROM {{ ref('future_population_mesh_500m') }}
WHERE substr(mesh_id, 1, 8) NOT IN (
    SELECT mesh_id FROM {{ ref('future_population_mesh') }}
)
