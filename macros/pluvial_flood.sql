{#
  雨水出水（内水）浸水想定区域データ（A51）の浸水深区分を数値に直すマクロ。

  区分（A51_005）は「水害ハザードマップ作成の手引き」の区分（詳細版）を基にした
  文字列だが、区域を設定するのは市町村等なので区切りの値は市区町村ごとに違う
  （「0.3m未満」「0.3m以上0.5m未満」「3m以上5m未満」など）。
  下限・上限だけ取り出して市区町村をまたいで比べられるようにする。
  読み取れない表記は NULL にする（区分の文字列は depth_label に残る）。
#}
{% macro pluvial_flood_depth_min(col) %}
  TRY_CAST(
    regexp_extract({{ col }}, '([0-9]+(\.[0-9]+)?)\s*[mｍ]?\s*以上', 1) AS DOUBLE
  )
{% endmacro %}
{% macro pluvial_flood_depth_max(col) %}
  TRY_CAST(
    regexp_extract({{ col }}, '([0-9]+(\.[0-9]+)?)\s*[mｍ]?\s*未満', 1) AS DOUBLE
  )
{% endmacro %}
