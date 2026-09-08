{#
  将来推計人口メッシュ（R6推計）の取り込みマクロ。

  全国版 Shapefile は都道府県別（01〜47）の 47 ファイルに分かれており、
  ST_Read は glob を受け付けないため、各ファイルを ST_Read して UNION ALL する。
  1km メッシュと 500m メッシュは属性体系が同じなので、粒度ごとの違いは
  データディレクトリとファイル名の接頭辞だけになる。
  raw 層を肥大化させないよう、後続で使うカラムのみを明示的に SELECT する。
    - MESH_ID  : 基準地域メッシュコード（1km は 8 桁、500m は 9 桁）
    - SHICODE  : 市区町村コード（複数市区町村にまたがるメッシュは "_" 連結）
    - PTN_YYYY : 推計年次別の総人口（2020〜2070、5年ごと。秘匿処理前の値）
    - PTC_YYYY : 65歳以上人口（高齢化率の算出用、2025/2050）
#}
{% macro future_population_mesh_source(data_dir='data/future_population', prefix='1km_mesh_2024') %}
  {%- set pop_years = [2020, 2025, 2030, 2035, 2040, 2045, 2050, 2055, 2060, 2065, 2070] -%}
  {%- set cols = ["MESH_ID", "SHICODE"] -%}
  {%- for y in pop_years -%}
    {%- do cols.append("PTN_" ~ y) -%}
  {%- endfor -%}
  {%- do cols.append("PTC_2025") -%}
  {%- do cols.append("PTC_2050") -%}
  {%- do cols.append("geom") -%}
  {%- set select_list = cols | join(", ") -%}
  {%- for i in range(1, 48) -%}
    {%- set nn = "%02d" | format(i) -%}
    {%- set path = data_dir ~ "/" ~ prefix ~ "_SHP/" ~ prefix ~ "_" ~ nn ~ "_SHP/" ~ prefix ~ "_" ~ nn ~ ".shp" -%}
    SELECT {{ select_list }} FROM ST_Read('{{ path }}')
    {%- if not loop.last %}
    UNION ALL
    {% endif -%}
  {%- endfor -%}
{% endmacro %}
