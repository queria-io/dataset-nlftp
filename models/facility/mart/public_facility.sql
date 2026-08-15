{{ config(materialized='table') }}

-- 市町村役場等及び公的集会施設の位置（ポイント）
SELECT
    admin_code,
    prefecture_code,
    prefecture_name,
    city_name,
    ward_name,
    facility_class_code,
    facility_class,
    facility_name,
    address,
    geometry
FROM {{ ref('stg_public_facility') }}
