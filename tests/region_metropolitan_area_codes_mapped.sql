-- 区域区分と区域コードは圏域ごとのコードリストから名称に変換している。
-- 原典に無いコードが現れると名称が NULL のまま公開されてしまうので、
-- 圏域・区域区分・区域コード・陸水等区分がすべて名称に変換できていることを検査する。
-- 2 つのコードが入る区域コードは、片方でも変換できなければ stg で名称を NULL にしている。
SELECT metropolitan_area_code, section_type_code, section_code, surface_type_code, count(*) AS row_count
FROM {{ ref('metropolitan_area') }}
WHERE metropolitan_area IS NULL
   OR section_type IS NULL
   OR surface_type IS NULL
   OR (section_code IS NULL) <> (section_type_code = '0')
   OR (section_code IS NOT NULL AND section_name IS NULL)
GROUP BY ALL
