-- 浸水深の区分は「水害ハザードマップ作成の手引き」の固定の語彙なので、
-- 下限も上限も読み取れない表記は現れないはず。表記が変わったまま
-- ビルドが通り、下限・上限とも NULL の行が公開されるのを防ぐ。
SELECT depth_label, count(*) AS row_count
FROM {{ ref('storm_surge_inundation') }}
WHERE depth_min_m IS NULL AND depth_max_m IS NULL
GROUP BY depth_label
