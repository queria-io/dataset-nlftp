{#
  市町村役場等及び公的集会施設データ（P05）のコード値を名称に変換するマクロ。

    - 施設分類（P05_002）: PubOfficeCd
#}
{% macro public_facility_class_name(col) %}
  CASE {{ col }}
    WHEN '1' THEN '本庁'
    WHEN '2' THEN '支所・出張所・連絡所'
    WHEN '3' THEN 'その他の行政サービス施設'
    WHEN '4' THEN '公立公民館'
    WHEN '5' THEN '集会施設'
  END
{% endmacro %}
