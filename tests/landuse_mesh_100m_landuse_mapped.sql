-- 土地利用種別は 17 種の固定コードで、原典に無いコードが現れると名称が NULL の
-- まま公開されてしまう。コードが全て名称に変換できていることを検査する。
SELECT landuse_code, count(*) AS mesh_count
FROM {{ ref('mesh_100m') }}
WHERE landuse IS NULL
GROUP BY landuse_code
