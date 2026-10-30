{{ config(tags=['isj']) }}

-- 列名を英字にし、座標とフラグを数値・真偽値にする。市区町村コードは原典に無い
SELECT
    -- 原典には都道府県名の末尾に数字が付いた行がある（24.0a の東京都で「東京都1」が 2 行）
    regexp_replace("都道府県名", '[0-9]+$', '') AS prefecture_name,
    "市区町村名" AS city_name,
    "大字・丁目名" AS oaza_chome_name,
    NULLIF("小字・通称名", '') AS koaza_name,
    "街区符号・地番" AS block_number,
    CAST("座標系番号" AS INTEGER) AS plane_rectangular_zone,
    CAST("Ｘ座標" AS DOUBLE) AS x,
    CAST("Ｙ座標" AS DOUBLE) AS y,
    CAST("緯度" AS DOUBLE) AS lat,
    CAST("経度" AS DOUBLE) AS lng,
    "住居表示フラグ" = '1' AS is_residential_address,
    "代表フラグ" = '1' AS is_representative,
    "更新前履歴フラグ" AS before_update_flag,
    "更新後履歴フラグ" AS after_update_flag,
    source_file
FROM {{ ref('raw_block') }}
