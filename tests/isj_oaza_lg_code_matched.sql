{{ config(severity='warn') }}

-- 大字・町丁目レベルの lg_code は原典の 5 桁のコードを市区町村マスタで 6 桁にする。
-- 市区町村マスタに無いコード（合併で無くなったコードなど）の行を挙げる
SELECT prefecture_code, city_name, count(*) AS row_count
FROM {{ ref('oaza') }}
WHERE lg_code IS NULL
GROUP BY prefecture_code, city_name
