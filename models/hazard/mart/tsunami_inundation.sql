{{ config(tags=['tsunami']) }}

-- 津波浸水想定区域のポリゴン（オープンデータ利用可の都道府県のみ）
--
-- 同じ県が複数の整備年度で提供されることがある。年度が違っても対象の海域が
-- 違うだけのことがあり（兵庫県は瀬戸内側が2016年度・日本海側が2018年度）、
-- 最新年度だけ残すと範囲が欠ける。逆に、同じ範囲を作り直しただけの年度は
-- そのまま並べると同じ場所が二重になる。旧年度の範囲が新しい年度の範囲に
-- 収まっているものだけを再整備とみなして落とし、はみ出す年度は残す。
-- 余裕は 0.001 度（約 100m）で、境界のわずかなずれで残さないようにする。
WITH extent AS (
    SELECT
        prefecture_code,
        data_year,
        min(ST_XMin(geometry)) AS xmin,
        min(ST_YMin(geometry)) AS ymin,
        max(ST_XMax(geometry)) AS xmax,
        max(ST_YMax(geometry)) AS ymax
    FROM {{ ref('stg_tsunami_inundation') }}
    GROUP BY 1, 2
),

superseded AS (
    SELECT older.prefecture_code, older.data_year
    FROM extent AS older
    JOIN extent AS newer
        ON newer.prefecture_code = older.prefecture_code
        AND newer.data_year > older.data_year
    WHERE older.xmin >= newer.xmin - 0.001
        AND older.ymin >= newer.ymin - 0.001
        AND older.xmax <= newer.xmax + 0.001
        AND older.ymax <= newer.ymax + 0.001
)

SELECT
    t.prefecture_code,
    {{ prefecture_name_from_code('t.prefecture_code') }} AS prefecture_name,
    t.data_year,
    t.depth_label,
    {{ tsunami_depth_min('t.depth_label') }} AS depth_min_m,
    {{ tsunami_depth_max('t.depth_label') }} AS depth_max_m,
    t.geometry
FROM {{ ref('stg_tsunami_inundation') }} AS t
WHERE NOT EXISTS (
    SELECT 1
    FROM superseded AS s
    WHERE s.prefecture_code = t.prefecture_code
        AND s.data_year = t.data_year
)
