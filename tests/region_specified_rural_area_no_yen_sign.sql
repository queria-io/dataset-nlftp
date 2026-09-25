-- 原典の名称には Shift_JIS の 0x5C 文字（十・能・予など）の後ろに円記号が
-- 混ざる。ステージングで取り除いているので、公開テーブルに残っていないことを
-- 検査する。
SELECT area_code
FROM {{ ref('specified_rural_area') }}
WHERE concat_ws('|', subprefecture_name, district_name, municipality_name,
                source_municipality_name, former_municipality_name) LIKE '%¥%'
