{{ config(tags=['large_fill']) }}

-- 大規模盛土造成地（谷埋め型・腹付け型の盛土造成地）のポリゴン
SELECT
    prefecture_code,
    {{ prefecture_name_from_code('prefecture_code') }} AS prefecture_name,
    municipality_code,
    municipality_name,
    fill_type_code,
    {{ large_fill_type_name('fill_type_code') }} AS fill_type,
    fill_number,
    geometry
FROM {{ ref('stg_large_fill_area') }}
