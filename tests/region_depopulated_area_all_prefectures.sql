-- 過疎地域は都道府県単位の zip 46 ファイルから作る。変換済み parquet は
-- スキップされるため、一部の県しか落ちていない状態でも行数が減るだけで
-- ビルドは通ってしまう。46 都道府県が揃っていることを検査する
-- （神奈川県には過疎地域の指定が無く、配布ファイルも存在しない）。
SELECT count(DISTINCT prefecture_code) AS prefecture_count
FROM {{ ref('depopulated_area') }}
HAVING count(DISTINCT prefecture_code) <> 46
