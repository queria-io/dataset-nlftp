{#
  過疎地域データ（A17）のコード値を名称に変換するマクロ。

    - 過疎区分コード（A17_009）: 指定の根拠条文（コードリスト KasoCode）
#}
{% macro depopulated_category_name(col) %}
  CASE {{ col }}
    WHEN 1 THEN '過疎市町村'
    WHEN 2 THEN '過疎地域とみなされる市町村'
    WHEN 3 THEN '過疎地域とみなされる区域'
  END
{% endmacro %}
