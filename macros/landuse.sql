{#
  都市地域土地利用細分メッシュ（L03-b-u）のコード値を名称に変換するマクロ。

    - 土地利用種別（L03b_u_002）: LandUseCd-09-u
#}
{% macro landuse_name(col) %}
  CASE {{ col }}
    WHEN '0100' THEN '田'
    WHEN '0200' THEN 'その他の農用地'
    WHEN '0500' THEN '森林'
    WHEN '0600' THEN '荒地'
    WHEN '0701' THEN '高層建物'
    WHEN '0702' THEN '工場'
    WHEN '0703' THEN '低層建物'
    WHEN '0704' THEN '低層建物（密集地）'
    WHEN '0901' THEN '道路'
    WHEN '0902' THEN '鉄道'
    WHEN '1001' THEN '公共施設等用地'
    WHEN '1002' THEN '空地'
    WHEN '1003' THEN '公園・緑地'
    WHEN '1100' THEN '河川地及び湖沼'
    WHEN '1400' THEN '海浜'
    WHEN '1500' THEN '海水域'
    WHEN '1600' THEN 'ゴルフ場'
  END
{% endmacro %}
