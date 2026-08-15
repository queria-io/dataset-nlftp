-- 市町村役場等及び公的集会施設は全国版 zip に入れ子で入った 47 都道府県分の zip から
-- 作る。取り込みが一部落ちても行数が減るだけでビルドは通ってしまうため、47 都道府県が
-- 揃っていることを検査する。
SELECT count(DISTINCT prefecture_code) AS prefecture_count
FROM {{ ref('public_facility') }}
HAVING count(DISTINCT prefecture_code) <> 47
