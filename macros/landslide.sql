{#
  土砂災害警戒区域データ（A33）のコード値を名称に変換するマクロ。

    - 現象種別コード（A33_001）: 土砂災害の現象の種類（コードリスト CodeOfPhenomenon）
    - 区域コード（A33_002）: 区域の種別と指定の状態（コードリスト CodeOfZone）。
      区域の種別（警戒区域／特別警戒区域）と、指定済みか基礎調査結果の公表段階かの
      2 つを 1 つのコードで持つので、分けて取り出せるようにする
#}
{% macro landslide_phenomenon_name(col) %}
  CASE {{ col }}
    WHEN 1 THEN '急傾斜地の崩壊'
    WHEN 2 THEN '土石流'
    WHEN 3 THEN '地滑り'
  END
{% endmacro %}
{% macro landslide_zone_type(col) %}
  CASE {{ col }}
    WHEN 1 THEN '土砂災害警戒区域'
    WHEN 2 THEN '土砂災害特別警戒区域'
    WHEN 3 THEN '土砂災害警戒区域'
    WHEN 4 THEN '土砂災害特別警戒区域'
  END
{% endmacro %}
{% macro landslide_is_designated(col) %}
  CASE {{ col }}
    WHEN 1 THEN true
    WHEN 2 THEN true
    WHEN 3 THEN false
    WHEN 4 THEN false
  END
{% endmacro %}
