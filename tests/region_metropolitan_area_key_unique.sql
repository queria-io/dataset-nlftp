-- 1 行 = 圏域・市区町村・区域・陸水等区分の組み合わせとして公開する。
-- ポリゴンをまとめ切れていないと面積の集計で二重に数えるので、
-- 組み合わせが重複していないことを検査する。
SELECT metropolitan_area_code, lg_code, section_type_code, section_code, surface_type_code, note
FROM {{ ref('metropolitan_area') }}
GROUP BY ALL
HAVING count(*) > 1
