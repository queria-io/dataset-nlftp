-- mart は市区町村の名称を any_value で取り出すので、同じ行政区域コードに
-- 別の市区町村名が混ざるとポリゴンと名称が食い違ったまま公開される。原典には
-- コードと名称がポリゴンの位置と合わない行があった（stg で直している）。
-- 集約する前の行で、同じ圏域・行政区域コードの名称が 1 つに揃っていることを検査する。
SELECT metropolitan_area_code, lg_code, list(DISTINCT municipality_name) AS municipality_names
FROM {{ ref('stg_metropolitan_area') }}
GROUP BY metropolitan_area_code, lg_code
HAVING count(DISTINCT municipality_name) > 1
    OR count(DISTINCT coalesce(district_name, '')) > 1
    OR count(DISTINCT prefecture_name) > 1
