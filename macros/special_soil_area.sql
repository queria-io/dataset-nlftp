{#
  特殊土壌地帯データ（A23）のコード値を名称に変換するマクロ。

    - 特殊土壌区分コード（A23_009）: 地帯を構成する特殊土壌の種類（コードリスト TokusyudojyoCd）
#}
{% macro special_soil_category_name(col) %}
  CASE {{ col }}
    WHEN 1 THEN 'シラス・ボラ・コラ・赤ホヤ・花崗岩風化土'
    WHEN 2 THEN '赤ホヤ・シラス・花崗岩風化土'
    WHEN 3 THEN '赤ホヤ'
    WHEN 4 THEN '赤ホヤ・花崗岩風化土'
    WHEN 5 THEN '花崗岩風化土'
    WHEN 6 THEN 'ヨナ・赤ホヤ・花崗岩風化土・シラス'
    WHEN 7 THEN '富士マサ'
    WHEN 8 THEN '赤ホヤ・ヨナ'
  END
{% endmacro %}
