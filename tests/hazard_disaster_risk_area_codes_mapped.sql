-- 指定主体区分と指定理由コードはコードリストで名称に直している。提供元がコードを
-- 増やすと名称が NULL になって黙って欠けるので、未変換が無いことを検査する。
SELECT prefecture_code, zone_name
FROM {{ ref('disaster_risk_area') }}
WHERE designating_body IS NULL OR reason IS NULL
