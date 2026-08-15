-- 市町村役場等及び公的集会施設は、原典に無い市区町村名を行政区域から LEFT JOIN で
-- 補っている。行政区域コードに対して市区町村名が一意でないと施設の行が静かに増える
-- ため、結合キーが一意であることを検査する。
SELECT lg_code, count(*) AS name_count
FROM (
    SELECT DISTINCT lg_code, city_name, ward_name
    FROM {{ ref('stg_administrative_boundary') }}
)
GROUP BY lg_code
HAVING count(*) > 1
