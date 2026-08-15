-- 施設分類は 5 種の固定コードで、原典に無いコードが現れると名称が NULL のまま
-- 公開されてしまう。コードが全て名称に変換できていることを検査する。
SELECT facility_class_code, count(*) AS facility_count
FROM {{ ref('public_facility') }}
WHERE facility_class IS NULL
GROUP BY facility_class_code
