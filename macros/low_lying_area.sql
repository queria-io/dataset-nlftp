{#
  低位地帯データ（G08）のコード値を名称に変換するマクロ。

    - 参照資料コード（G08_003）: 低位地帯の抽出に使った標高 DEM の種類（コードリスト ReferenceDataCd）
#}
{% macro lowland_reference_data_name(col) %}
  CASE {{ col }}
    WHEN '1' THEN '10mDEM'
    WHEN '2' THEN '5m空中写真DEM'
    WHEN '3' THEN '5mレーザDEM'
    WHEN '4' THEN '2mDEM'
    WHEN '5' THEN '混在（10m含む）'
    WHEN '6' THEN '混在（10m含まない）'
  END
{% endmacro %}
