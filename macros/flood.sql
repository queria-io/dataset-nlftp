{#
  洪水浸水想定区域データ（A31a）のコード値を名称に変換するマクロ。

    - 浸水深ランク（A31a_205）: 浸水深の区分コード（1〜6）
#}
{% macro flood_depth_label(col) %}
  CASE {{ col }}
    WHEN 1 THEN '0.5m未満'
    WHEN 2 THEN '0.5m以上3m未満'
    WHEN 3 THEN '3m以上5m未満'
    WHEN 4 THEN '5m以上10m未満'
    WHEN 5 THEN '10m以上20m未満'
    WHEN 6 THEN '20m以上'
  END
{% endmacro %}
