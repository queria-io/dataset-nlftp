-- 参照資料コードは 6 種の固定コードで、原典に無いコードが現れると名称が NULL の
-- まま公開されてしまう。コードが全て名称に変換できていることを検査する。
SELECT reference_data_code, count(*) AS area_count
FROM {{ ref('low_lying_area') }}
WHERE reference_data IS NULL
GROUP BY reference_data_code
