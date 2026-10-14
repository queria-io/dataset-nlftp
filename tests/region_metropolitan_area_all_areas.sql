-- 三大都市圏計画区域は圏域単位の zip 3 ファイルから作る。変換済み parquet は
-- スキップされるため、一部の圏域しか落ちていない状態でも行数が減るだけで
-- ビルドは通ってしまう。3 圏域が揃っていることを検査する。
SELECT count(DISTINCT metropolitan_area_code) AS area_count
FROM {{ ref('metropolitan_area') }}
HAVING count(DISTINCT metropolitan_area_code) <> 3
