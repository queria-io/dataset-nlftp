-- 250mメッシュは500mメッシュと同じ推計を細かい粒度で集計し直したもので、
-- メッシュコードの先頭9桁が500mメッシュのコードになる。粒度をまたいだ結合は
-- この桁で行うため、対応が崩れていないことを検査する。
SELECT DISTINCT substr(m.mesh_id, 1, 9) AS mesh_500m_code
FROM {{ ref('future_population_mesh_250m') }} AS m
WHERE NOT EXISTS (
    SELECT 1
    FROM {{ ref('future_population_mesh_500m') }} AS h
    WHERE h.mesh_id = substr(m.mesh_id, 1, 9)
)
