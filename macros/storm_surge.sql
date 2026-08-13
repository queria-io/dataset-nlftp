{#
  高潮浸水想定区域データ（A49）の浸水深区分を数値に直すマクロ。

  区分（A49_003）は「水害ハザードマップ作成の手引き」の区分（詳細版）を基にした
  文字列で、「0.3m未満」「0.3m以上0.5m未満」「20m以上」のように書かれる。
  下限・上限だけ取り出して区分をまたいで比べられるようにする。
  読み取れない表記は NULL にする（区分の文字列は depth_label に残る）。
#}
{% macro storm_surge_depth_min(col) %}
  TRY_CAST(
    regexp_extract({{ col }}, '([0-9]+(\.[0-9]+)?)\s*[mｍ]?\s*以上', 1) AS DOUBLE
  )
{% endmacro %}
{% macro storm_surge_depth_max(col) %}
  TRY_CAST(
    regexp_extract({{ col }}, '([0-9]+(\.[0-9]+)?)\s*[mｍ]?\s*未満', 1) AS DOUBLE
  )
{% endmacro %}
