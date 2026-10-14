{{ config(materialized='table') }}

-- 1 行 = 圏域・市区町村・区域・陸水等区分の組み合わせ。原典は同じ組み合わせを
-- 島や飛び地ごとのポリゴンに分けて持つので、まとめて 1 つのマルチポリゴンにする。
-- 市区町村の名称はどのポリゴンにも同じ値が入っているため any_value で取り出す
SELECT
    metropolitan_area_code,
    {{ metropolitan_area_name('metropolitan_area_code') }} AS metropolitan_area,
    lg_code,
    left(lg_code, 2) AS prefecture_code,
    any_value(prefecture_name) AS prefecture_name,
    any_value(district_name) AS district_name,
    any_value(municipality_name) AS municipality_name,
    section_type_code,
    {{ metropolitan_section_type_name('metropolitan_area_code', 'section_type_code') }} AS section_type,
    section_code,
    any_value(section_name) AS section_name,
    surface_type_code,
    {{ metropolitan_surface_type_name('surface_type_code') }} AS surface_type,
    note,
    -- 原典に面積の属性は無いので、ポリゴンから回転楕円体上の面積を計算する。
    -- ST_Area_Spheroid は (緯度, 経度) の順を前提にするので座標を入れ替える
    ST_Area_Spheroid(ST_FlipCoordinates(ST_Union_Agg(geometry))) / 1e6 AS area_km2,
    ST_Union_Agg(geometry) AS geometry
FROM {{ ref('stg_metropolitan_area') }}
GROUP BY
    metropolitan_area_code,
    lg_code,
    section_type_code,
    section_code,
    surface_type_code,
    note
