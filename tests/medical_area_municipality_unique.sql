-- 対応表は 1 行 = 1 市区町村として公開する。原典は市区町村ごとに複数のポリゴンを
-- 持ち、属性だけを一意にして作るので、市区町村名や医療圏の表記がポリゴン間で
-- 揺れると 1 つの市区町村が複数行に分かれる。結合したときに二重に数えるので、
-- 行政区域コードが重複していないことを確かめる。
SELECT admin_code
FROM {{ ref('medical_area_municipality') }}
GROUP BY admin_code
HAVING count(*) > 1
