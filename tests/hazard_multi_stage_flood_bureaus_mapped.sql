-- 地方整備局等コードは配布ファイル名の 2 桁で、対応表を macros に持っている。
-- 配布単位が増えたときに名称の無い行が公開されるのを防ぐ。
SELECT bureau_code, count(*) AS row_count
FROM {{ ref('multi_stage_flood_inundation') }}
WHERE bureau_name IS NULL
GROUP BY bureau_code
