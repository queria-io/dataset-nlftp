{{ config(tags=['isj']) }}

-- 列名を英字にし、座標を数値にする。市区町村コードは 5 桁（チェックディジット無し）
SELECT
    "都道府県コード" AS prefecture_code,
    "都道府県名" AS prefecture_name,
    "市区町村コード" AS city_code,
    "市区町村名" AS city_name,
    "大字町丁目コード" AS oaza_chome_code,
    "大字町丁目名" AS oaza_chome_name,
    CAST("緯度" AS DOUBLE) AS lat,
    CAST("経度" AS DOUBLE) AS lng,
    "原典資料コード" AS source_material_code,
    "大字・字・丁目区分コード" AS oaza_chome_class_code,
    source_file
FROM {{ ref('raw_oaza') }}
