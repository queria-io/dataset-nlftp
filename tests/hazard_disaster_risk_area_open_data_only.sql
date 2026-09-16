-- 災害危険区域は指定した地方公共団体ごとに公開条件が異なる。「オープンデータにて
-- 公開」とされた団体が指定した区域以外が混ざっていないことを確かめる。
-- 一覧の行と地物の対応は指定主体で決まり、都道府県指定なら県の行（行政CD が
-- <都道府県コード>000）、市町村指定なら代表行政コードの行を見る。
WITH designated AS (
    SELECT DISTINCT
        CASE
            WHEN designating_body = '都道府県' THEN prefecture_code || '000'
            ELSE municipality_code
        END AS admin_code
    FROM {{ ref('disaster_risk_area') }}
)
SELECT d.admin_code
FROM designated AS d
LEFT JOIN {{ ref('raw_disaster_risk_area_terms') }} AS t
    ON d.admin_code = t.admin_code
WHERE t.disclosure IS DISTINCT FROM 'オープンデータにて公開'
