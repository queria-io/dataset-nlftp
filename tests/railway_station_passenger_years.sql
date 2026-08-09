-- 原典は年度ごとの4列（重複コード・データ有無コード・備考・乗降客数）を繰り返す
-- 並びで、モデルはその規則に沿って縦持ちに戻す。並びが変わると年度と値の対応が
-- ずれるため、2011〜2024年度が揃い、どの年度にも乗降客数が入っていることを検査する。
SELECT y AS year
FROM range(2011, 2025) AS t (y)
WHERE y NOT IN (
    SELECT year FROM {{ ref('station_passenger') }} WHERE passenger_count IS NOT NULL
)
