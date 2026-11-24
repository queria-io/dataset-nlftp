{{ config(materialized='table') }}

-- 政令指定都市の区を市レベルに統合し、非政令市とあわせて出力
-- ABR 市区町村マスタで区コード→市コードを解決し、lg_code で GROUP BY
-- 東京23区（特別区）は独立した地方公共団体のため統合しない
WITH city_codes AS (
    SELECT LEFT(lg_code, 5) AS lg_code, pref, city
    FROM {{ ref('stg_mt_city') }}
    WHERE ward IS NULL AND city IS NOT NULL
),
ward_to_city AS (
    SELECT LEFT(w.lg_code, 5) AS ward_lg_code, c.lg_code AS city_lg_code
    FROM {{ ref('stg_mt_city') }} w
    JOIN city_codes c ON w.pref = c.pref AND w.city = c.city
    WHERE w.ward IS NOT NULL
),
designated AS (
    SELECT
        wc.city_lg_code AS lg_code,
        m.prefecture_code,
        m.prefecture_name,
        m.county_name,
        m.city_name,
        ST_Union_Agg(m.geometry) AS geometry
    FROM {{ ref('municipality') }} m
    JOIN ward_to_city wc ON m.lg_code = wc.ward_lg_code
    GROUP BY wc.city_lg_code, m.prefecture_code, m.prefecture_name,
             m.county_name, m.city_name
),
non_designated AS (
    SELECT
        lg_code,
        prefecture_code,
        prefecture_name,
        county_name,
        city_name,
        geometry
    FROM {{ ref('municipality') }}
    WHERE ward_name IS NULL
)
SELECT * FROM designated
UNION ALL
SELECT * FROM non_designated
