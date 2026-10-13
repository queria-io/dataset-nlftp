{{ config(materialized='table', tags=['lake']) }}

-- 1 行 = 1 湖沼。湖沼の範囲は複数の市区町村・都道府県にまたがることがあるので、
-- 行政区域コードと都道府県コードはリストで持つ
SELECT
    record_number,
    lake_name,
    lg_codes,
    list_sort(list_distinct(list_transform(lg_codes, x -> x[1:2]))) AS prefecture_codes,
    max_depth_m,
    water_surface_elevation_m,
    -- 原典に面積の属性は無いので、ポリゴンから回転楕円体上の面積を計算する。
    -- ST_Area_Spheroid は (緯度, 経度) の順を前提にするので座標を入れ替える
    ST_Area_Spheroid(ST_FlipCoordinates(geometry)) / 1e6 AS area_km2,
    geometry
FROM {{ ref('stg_lake') }}
