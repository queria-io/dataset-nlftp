{#
  バス停留所データ（P11）のコード値を名称に変換するマクロ。

    - バス区分コード（P11_004_01〜35）: BusCd
#}
{% macro bus_class_name(col) %}
  CASE {{ col }}
    WHEN '1' THEN '路線バス（民間）'
    WHEN '2' THEN '路線バス（公営）'
    WHEN '3' THEN 'コミュニティバス'
    WHEN '4' THEN 'デマンドバス'
    WHEN '5' THEN 'その他'
  END
{% endmacro %}
