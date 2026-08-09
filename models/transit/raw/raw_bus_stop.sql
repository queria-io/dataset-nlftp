{{ config(materialized='table') }}

-- バス停留所は都道府県別の GeoJSON で配布されるため、ST_Read を 47 本 UNION ALL する
-- （ST_Read は glob 非対応）。都道府県コードはファイル名にしか無いのでここで列にする。
{% for code in range(1, 48) %}
{% set pref = '%02d' | format(code) %}
SELECT '{{ pref }}' AS prefecture_code, *
FROM ST_Read('data/transit/P11-22_{{ pref }}.geojson')
{% if not loop.last %}UNION ALL{% endif %}
{% endfor %}
