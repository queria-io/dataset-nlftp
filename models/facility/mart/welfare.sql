{{ config(materialized='table') }}

-- 福祉施設の代表点（ポイント）
SELECT
    prefecture,
    city,
    admin_code,
    address,
    major_class_code,
    major_class,
    middle_class_code,
    middle_class,
    minor_class_code,
    minor_class,
    institution_name,
    administrator_code,
    administrator,
    position_accuracy_code,
    position_accuracy,
    geometry
FROM {{ ref('stg_welfare') }}
