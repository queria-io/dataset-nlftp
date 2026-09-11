{{ config(tags=['multi_stage_flood']) }}

-- 多段階浸水想定のポリゴン
--
-- 1 行 = 水系 × 降雨規模 × 浸水深の区分のポリゴン。同じ場所が降雨規模の数だけ
-- 重なって入るので、面積や件数を出すときは降雨規模を 1 つに絞る。
-- 同じ水系コードでも対象区間が違えば別の行になる（水系名のかっこ書きで分かれる）。
SELECT
    bureau_code,
    {{ multi_stage_flood_bureau_name('bureau_code') }} AS bureau_name,
    river_system_code,
    river_system_name,
    data_year,
    rainfall_probability_denominator,
    depth_rank_3,
    {{ multi_stage_flood_depth_rank_3_label('depth_rank_3') }} AS depth_rank_3_label,
    depth_rank_6,
    {{ multi_stage_flood_depth_rank_6_label('depth_rank_6') }} AS depth_rank_6_label,
    {{ multi_stage_flood_depth_min('depth_rank_6', 'depth_rank_3') }} AS depth_min_m,
    {{ multi_stage_flood_depth_max('depth_rank_6', 'depth_rank_3') }} AS depth_max_m,
    geometry
FROM {{ ref('stg_multi_stage_flood_inundation') }}
