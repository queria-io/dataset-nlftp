{#
  大規模盛土造成地データ（A54）のコード値を名称に変換するマクロ。

    - 盛土区分（A54_001）: 盛土造成地の型（コードリスト 盛土区分コード）
#}
{% macro large_fill_type_name(col) %}
  CASE {{ col }}
    WHEN '1' THEN '谷埋め型'
    WHEN '2' THEN '腹付け型'
    WHEN '9' THEN '区分をしていない'
  END
{% endmacro %}
