{#
  災害危険区域データ（A48）のコード値を名称に変換するマクロ。

    - 指定主体区分（A48_004）: 区域を指定した地方公共団体の区分。災害危険区域は
      都道府県と市町村のどちらも指定できる
    - 指定理由コード（A48_007）: 区域を指定した理由。詳細は指定理由（A48_008）に
      地方公共団体の表記のまま入る
#}
{% macro disaster_risk_area_designating_body(col) %}
  CASE {{ col }}
    WHEN '1' THEN '都道府県'
    WHEN '2' THEN '市町村'
  END
{% endmacro %}

{% macro disaster_risk_area_reason(col) %}
  CASE {{ col }}
    WHEN '1' THEN '水害（河川）'
    WHEN '2' THEN '水害（海）'
    WHEN '3' THEN '水害（河川・海）'
    WHEN '4' THEN '急傾斜地崩壊等'
    WHEN '5' THEN '地すべり等'
    WHEN '6' THEN '火山被害'
    WHEN '7' THEN 'その他'
  END
{% endmacro %}
