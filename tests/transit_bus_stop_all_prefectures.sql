-- バス停留所は都道府県別ファイルを 47 本 UNION ALL して作る。取り込みが一部
-- 落ちても行数が減るだけでビルドは通ってしまうため、47 都道府県が揃っていることを検査する。
SELECT count(DISTINCT prefecture_code) AS prefecture_count
FROM {{ ref('bus_stop') }}
HAVING count(DISTINCT prefecture_code) <> 47
