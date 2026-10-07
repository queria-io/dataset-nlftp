-- 盛土区分は 3 種の固定コードで、原典に無いコードが現れると名称が NULL の
-- まま公開されてしまう。コードが全て名称に変換できていることを検査する。
SELECT fill_type_code, count(*) AS area_count
FROM {{ ref('large_fill_area') }}
WHERE fill_type IS NULL
GROUP BY fill_type_code
