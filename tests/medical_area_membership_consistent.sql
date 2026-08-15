-- 二次医療圏の構成市区町村は、二次医療圏データ（カンマ区切りの一覧）と
-- 一次医療圏データ（市区町村ごとの行）の 2 か所に入っている。公開する対応表は
-- 後者から作るので、前者と食い違いが無いことを確かめる。
WITH from_secondary AS (
    SELECT DISTINCT
        area_code,
        trim(member_code) AS admin_code
    FROM {{ ref('raw_secondary_medical_area') }},
        unnest(string_split(member_admin_codes, ',')) AS t(member_code)
),

from_primary AS (
    SELECT DISTINCT
        secondary_area_code AS area_code,
        admin_code
    FROM {{ ref('medical_area_municipality') }}
),

missing_in_primary AS (
    SELECT * FROM from_secondary
    EXCEPT
    SELECT * FROM from_primary
),

missing_in_secondary AS (
    SELECT * FROM from_primary
    EXCEPT
    SELECT * FROM from_secondary
)

SELECT * FROM missing_in_primary
UNION ALL
SELECT * FROM missing_in_secondary
