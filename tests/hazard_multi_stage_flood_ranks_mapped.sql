-- 浸水深ランクは 3 段階（1〜3）と 6 段階（1〜6）の固定のコードリストなので、
-- ラベルに引けないコードは現れないはず。区分の追加や原典の値の揺れを
-- そのまま公開しないために止める。
SELECT depth_rank_3, depth_rank_6, count(*) AS row_count
FROM {{ ref('multi_stage_flood_inundation') }}
WHERE (depth_rank_3 IS NOT NULL AND depth_rank_3_label IS NULL)
   OR (depth_rank_6 IS NOT NULL AND depth_rank_6_label IS NULL)
GROUP BY depth_rank_3, depth_rank_6
