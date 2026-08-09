{{ config(materialized='table') }}

-- 元データは 1 行 = 1 駅（路線ごと）で、年度ごとの乗降客数を横持ちで持つ。
-- 年度は S12_006〜S12_009（2011年度）を起点に 4 列ずつ繰り返す並びなので、
-- 年度を縦持ちに正規化する。
{% set first_year = 2011 %}
{% set last_year = 2024 %}

{% for year in range(first_year, last_year + 1) %}
{% set base = 6 + 4 * (year - first_year) %}
SELECT
    S12_001 AS station_name,
    S12_001c AS station_code,
    S12_001g AS station_group_code,
    S12_002 AS operator,
    S12_003 AS line_name,
    CAST(S12_004 AS VARCHAR) AS railway_class_code,
    {{ railway_class_name('CAST(S12_004 AS VARCHAR)') }} AS railway_class,
    CAST(S12_005 AS VARCHAR) AS operator_type_code,
    {{ operator_type_name('CAST(S12_005 AS VARCHAR)') }} AS operator_type,
    {{ year }} AS year,
    CAST(S12_{{ '%03d' % base }} AS VARCHAR) AS duplicate_code,
    {{ railway_duplicate_name('CAST(S12_%03d AS VARCHAR)' % base) }} AS duplicate_status,
    CAST(S12_{{ '%03d' % (base + 1) }} AS VARCHAR) AS data_availability_code,
    {{ railway_data_availability_name('CAST(S12_%03d AS VARCHAR)' % (base + 1)) }} AS data_availability,
    NULLIF(S12_{{ '%03d' % (base + 2) }}, '') AS note,
    S12_{{ '%03d' % (base + 3) }} AS passenger_count,
    ST_MakeValid(geom) AS geometry
FROM {{ ref('raw_station_passenger') }}
WHERE geom IS NOT NULL
{% if not loop.last %}
UNION ALL
{% endif %}
{% endfor %}
