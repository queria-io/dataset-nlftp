{#
  津波浸水想定データ（A40）の浸水深区分を数値に直すマクロ。

  区分（A40_003）は各都道府県の報告書の表記をそのまま持つ文字列で、
  区切りの値も書き方も県ごとに違う（「0.01m以上 ～ 0.3m未満」「0.3m未満」
  「～ 0.3m未満」「5m以上」「1.0m以上 ～ 3.0m未満」など）。
  下限・上限だけ取り出して県をまたいで比べられるようにする。
  読み取れない表記は NULL にする（区分の文字列は depth_label に残る）。
#}
{% macro tsunami_depth_min(col) %}
  TRY_CAST(
    regexp_extract({{ col }}, '([0-9]+(\.[0-9]+)?)\s*[mｍ]?\s*以上', 1) AS DOUBLE
  )
{% endmacro %}
{% macro tsunami_depth_max(col) %}
  TRY_CAST(
    regexp_extract({{ col }}, '([0-9]+(\.[0-9]+)?)\s*[mｍ]?\s*未満', 1) AS DOUBLE
  )
{% endmacro %}
