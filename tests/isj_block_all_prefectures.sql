-- 街区レベル位置参照情報は都道府県別の zip を 47 本取り込んで作る。取り込みが一部
-- 落ちても行数が減るだけでビルドは通ってしまうため、47 都道府県が揃っていることを検査する。
SELECT count(DISTINCT prefecture_name) AS prefecture_count
FROM {{ ref('block') }}
HAVING count(DISTINCT prefecture_name) <> 47
