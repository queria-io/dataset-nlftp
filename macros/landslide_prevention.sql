{#
  地すべり防止区域データ（A46）のコード値を名称に変換するマクロ。

    - 所管省庁コード（A46-?_009）: 区域を所管する省庁。地すべり防止区域は
      指定の根拠となる地すべりの態様によって所管が 3 つに分かれる
#}
{% macro landslide_prevention_agency_name(col) %}
  CASE {{ col }}
    WHEN 1 THEN '国土交通省'
    WHEN 2 THEN '農林水産省農村振興局'
    WHEN 3 THEN '林野庁'
  END
{% endmacro %}
