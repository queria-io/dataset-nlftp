-- バスルートのステージング。令和4年度版の属性は事業者名と備考のみで、
-- 備考（N07_002）は全件が空のため落とす。
SELECT
    N07_001 AS operator,
    ST_MakeValid(geom) AS geometry
FROM {{ ref('raw_bus_route') }}
WHERE geom IS NOT NULL
