-- 特殊土壌地帯は都道府県単位の zip 14 ファイルから作る。変換済み parquet は
-- スキップされるため、一部の県しか落ちていない状態でも行数が減るだけで
-- ビルドは通ってしまう。指定のある 14 県が揃っていることを検査する。
SELECT count(DISTINCT prefecture_code) AS prefecture_count
FROM {{ ref('special_soil_area') }}
HAVING count(DISTINCT prefecture_code) <> 14
