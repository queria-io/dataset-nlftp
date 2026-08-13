{{ config(tags=['storm_surge']) }}

-- 高潮浸水想定区域のポリゴン（オープンデータ利用可の都道府県のみ）
--
-- 同じ県が複数の整備年度で提供される。提供元は「過年度整備分と合わせて利用し、
-- 重複する箇所は最新年度を使う」としたうえで、2023年度以降のデータは過年度分を
-- 最新年度に統合したと注記している。統合済みの年度があればそれだけを残し、
-- 無い県は過年度分が互いを補うのでそのまま並べる。
WITH integrated AS (
    SELECT prefecture_code, max(data_year) AS data_year
    FROM {{ ref('stg_storm_surge_inundation') }}
    GROUP BY 1
    HAVING max(data_year) >= 2023
)

SELECT
    s.prefecture_code,
    {{ prefecture_name_from_code('s.prefecture_code') }} AS prefecture_name,
    s.data_year,
    s.depth_label,
    {{ storm_surge_depth_min('s.depth_label') }} AS depth_min_m,
    {{ storm_surge_depth_max('s.depth_label') }} AS depth_max_m,
    s.geometry
FROM {{ ref('stg_storm_surge_inundation') }} AS s
LEFT JOIN integrated AS i ON i.prefecture_code = s.prefecture_code
WHERE i.prefecture_code IS NULL OR s.data_year = i.data_year
