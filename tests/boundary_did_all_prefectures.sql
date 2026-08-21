-- 人口集中地区は全国版 zip 1 ファイルから作る。ダウンロードや変換が途中で
-- 欠けても行数が減るだけでビルドは通ってしまうため、47 都道府県が揃って
-- いることを検査する。
SELECT count(DISTINCT prefecture_code) AS prefecture_count
FROM {{ ref('did') }}
HAVING count(DISTINCT prefecture_code) <> 47
