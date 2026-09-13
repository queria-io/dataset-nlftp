-- 過疎区分は 3 種の固定コードで、原典に無いコードが現れると区分名が NULL の
-- まま公開されてしまう。コードが全て名称に変換できていることを検査する。
SELECT category_code, count(*) AS area_count
FROM {{ ref('depopulated_area') }}
WHERE category IS NULL
GROUP BY category_code
