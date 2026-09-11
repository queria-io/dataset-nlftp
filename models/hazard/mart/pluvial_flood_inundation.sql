{{ config(tags=['pluvial_flood']) }}

-- 雨水出水（内水）浸水想定区域のポリゴン
--
-- 区域を設定するのは市町村等なので、収録の単位も市区町村になる。
-- 配布は都道府県単位の zip だが、新しい配布年度の zip が過年度分を含んだ
-- 最新の状態なので、パイプラインが都道府県ごとに最新の配布年度だけを取り込む。
-- 整備年度（data_year）は市区町村ごとに違うため、ここでは絞り込まない。
SELECT
    prefecture_code,
    {{ prefecture_name_from_code('prefecture_code') }} AS prefecture_name,
    admin_code,
    municipality_name,
    data_year,
    depth_label,
    {{ pluvial_flood_depth_min('depth_label') }} AS depth_min_m,
    {{ pluvial_flood_depth_max('depth_label') }} AS depth_max_m,
    geometry
FROM {{ ref('stg_pluvial_flood_inundation') }}
