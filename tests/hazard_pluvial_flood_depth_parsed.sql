-- 浸水深の区分は「水害ハザードマップ作成の手引き」の固定の語彙なので、
-- 下限も上限も読み取れない表記は現れないはず。区域を設定するのは市町村等で
-- 表記が揺れる経路があるため、揺れたまま下限・上限とも NULL の行が公開される
-- のを防ぐ。
SELECT depth_label, count(*) AS row_count
FROM {{ ref('pluvial_flood_inundation') }}
WHERE depth_min_m IS NULL AND depth_max_m IS NULL
GROUP BY depth_label
