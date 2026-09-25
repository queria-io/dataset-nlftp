-- 1 行 = 1 指定区域として公開する。原典は区域を島や飛び地ごとのポリゴンに
-- 分けて持つので、特定農山村ID でまとめ切れていないと市町村別の集計で二重に
-- 数える。特定農山村地域コードが重複していないことを検査する。
SELECT area_code
FROM {{ ref('specified_rural_area') }}
GROUP BY area_code
HAVING count(*) > 1
