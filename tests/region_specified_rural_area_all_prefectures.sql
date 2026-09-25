-- 特定農山村地域は都道府県単位の zip 47 ファイルから作る。変換済み parquet は
-- スキップされるため、一部の県しか落ちていない状態でも行数が減るだけで
-- ビルドは通ってしまう。47 都道府県が揃っていることを検査する。
SELECT count(DISTINCT prefecture_code) AS prefecture_count
FROM {{ ref('specified_rural_area') }}
HAVING count(DISTINCT prefecture_code) <> 47
