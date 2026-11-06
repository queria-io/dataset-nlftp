-- 平成22年度（10.0a）から今の版までの街区レベル位置参照情報を、名前と番号
-- （都道府県名・市区町村名・大字・丁目名・小字・通称名・街区符号・地番）ごとに 1 行にする。
-- 点は最後に載った版の点。同じ名前と番号でも版ごとに座標がわずかにずれる行が多いので、
-- 点の違いでは行を分けない。
--
-- 過去の版は変わらないので、毎回は読まない。Sync のたびに今の版だけを名前と番号で merge する。
-- - 今の版にもある名前と番号: 最後に載った版と点を今の版で上書きする（行は増えない）
-- - 今の版で初めて現れた名前と番号: 行を追加する
-- - 今の版に無い名前と番号: そのまま残す
-- 過去の版（2.6 億行）を読むのは、表が無いときと --full-refresh のときだけ。
-- そのときはスレッドごとに集約の表を持つと一時ファイルが 20GB を超えるので、1 スレッドで作る
-- （merge で今の版だけを読むときはスレッドを絞らない）
--
-- 名前と番号の列は空 (NULL) の行があり、= では一致しない（一致しないと merge のたびに
-- 同じ名前と番号の行が増える）。prefecture_name は valid で NULL を除いているので
-- unique_key に置き、残りの列は IS NOT DISTINCT FROM で突き合わせる
{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['prefecture_name'],
    incremental_predicates=[
        "DBT_INTERNAL_SOURCE.city_name IS NOT DISTINCT FROM DBT_INTERNAL_DEST.city_name",
        "DBT_INTERNAL_SOURCE.oaza_chome_name IS NOT DISTINCT FROM DBT_INTERNAL_DEST.oaza_chome_name",
        "DBT_INTERNAL_SOURCE.koaza_name IS NOT DISTINCT FROM DBT_INTERNAL_DEST.koaza_name",
        "DBT_INTERNAL_SOURCE.block_number IS NOT DISTINCT FROM DBT_INTERNAL_DEST.block_number",
    ],
    merge_exclude_columns=['first_edition_year'],
    tags=['isj'],
    pre_hook="{% if not is_incremental() %}SET threads = 1{% endif %}",
    post_hook="RESET threads",
) }}

WITH editions AS (
    SELECT * FROM {{ ref('raw_block') }}
    {% if not is_incremental() %}
    UNION ALL BY NAME
    SELECT * FROM {{ source('isj_files', 'block_history') }}
    {% endif %}
),
rows AS (
    SELECT
        regexp_replace("都道府県名", '[0-9]+$', '') AS prefecture_name,
        "市区町村名" AS city_name,
        "大字・丁目名" AS oaza_chome_name,
        NULLIF("小字・通称名", '') AS koaza_name,
        "街区符号・地番" AS block_number,
        "住居表示フラグ" = '1' AS is_residential_address,
        "代表フラグ" = '1' AS is_representative,
        CAST("緯度" AS DOUBLE) AS lat,
        CAST("経度" AS DOUBLE) AS lng,
        -- 版の年はファイル名の年（10.0a は <都道府県コード>_2011.csv）
        CAST(regexp_extract(source_file, '_([0-9]{4})\.[cC][sS][vV]$', 1) AS INTEGER) AS edition_year
    FROM editions
    -- 履歴フラグの 3 は削除された街区符号・地番。block と同じく除く
    WHERE "更新前履歴フラグ" IS DISTINCT FROM '3'
        AND "更新後履歴フラグ" IS DISTINCT FROM '3'
),
-- 原典には列が崩れた行がある（17.0a の北海道・秋田県で名前が空の 7 行、大阪府で
-- 都道府県名が「大阪市」の 39 行）。都道府県名が都道府県でない行は使わない
valid AS (
    SELECT * FROM rows
    WHERE prefecture_name IN (SELECT pref FROM {{ ref('raw_mt_city') }})
        -- CP932 として読めなかったバイトは U+FFFD にして取り込んでいる（pipelines/isj.py）。
        -- 名前に残すとその版だけの別の名前と番号になり、今の版から消えた住所に見えるので使わない
        AND NOT contains(
            concat_ws('|', city_name, oaza_chome_name, koaza_name, block_number), chr(65533)
        )
),
merged AS (
    SELECT
        prefecture_name,
        city_name,
        oaza_chome_name,
        koaza_name,
        block_number,
        min(edition_year) AS first_edition_year,
        max(edition_year) AS last_edition_year,
        -- 最後に載った版の点。同じ版で複数の地点に分かれるときは代表フラグの行
        arg_max(
            {'lat': lat, 'lng': lng, 'is_residential_address': is_residential_address},
            -- 代表フラグでも決まらないときに、ビルドごとに点が変わらないよう座標で決める
            (edition_year, is_representative, lat, lng)
        ) AS last
    FROM valid
    GROUP BY ALL
),
-- block と同じ規則で、今の市区町村名に一致する行にだけ lg_code を付ける
cities AS (
{{ isj_city_names() }}
)
SELECT
    c.lg_code,
    m.prefecture_name,
    m.city_name,
    m.oaza_chome_name,
    m.koaza_name,
    m.block_number,
    m.first_edition_year,
    m.last_edition_year,
    m.last.is_residential_address AS is_residential_address,
    m.last.lat AS lat,
    m.last.lng AS lng,
    ST_Point(m.last.lng, m.last.lat) AS geometry
FROM merged m
LEFT JOIN cities c ON c.pref = m.prefecture_name AND c.name = m.city_name
{% if not is_incremental() %}
ORDER BY c.lg_code, m.oaza_chome_name, m.koaza_name, m.block_number
{% endif %}
