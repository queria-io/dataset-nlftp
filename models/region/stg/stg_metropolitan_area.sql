-- 原典の属性には、ポリゴンの位置と合わない行がある。行政区域（2025年版）と
-- 重ねて、ポリゴンの側を正として直す。
--   - 中部圏の御浜町のポリゴン（88km²）に紀宝町のコード 24562 が入っている。
--     御浜町は 24561
--   - 首都圏の 14136（川崎市宮前区）のポリゴンの 1 つに、名称が横浜市都筑区で
--     入っている。ポリゴンは宮前区の範囲にある
--   - 近畿圏の四條畷市の 1 行だけ「四条畷市」と表記が違う
--
-- 中部圏の保全区域と都市整備区域が重なる部分（区域区分 4）は、区域コードに
-- 「C01,C03AK」のように 2 つのコードがカンマ区切りで入る。名称はコードごとに
-- 引いてつなぐ。1 つでも名称に変換できないコードがあれば NULL にして、
-- 片方の名称だけで公開されないようにする
WITH fixed AS (
    SELECT
        metropolitan_area_code,
        CASE
            WHEN metropolitan_area_code = 'CHUBU' AND lg_code = '24562' AND municipality_name = '御浜町'
                THEN '24561'
            ELSE lg_code
        END AS lg_code,
        prefecture_name,
        CASE
            WHEN metropolitan_area_code = 'SYUTO' AND lg_code = '14136' AND municipality_name = '都筑区'
                THEN '川崎市'
            ELSE district_name
        END AS district_name,
        CASE
            WHEN metropolitan_area_code = 'SYUTO' AND lg_code = '14136' AND municipality_name = '都筑区'
                THEN '宮前区'
            WHEN municipality_name = '四条畷市' THEN '四條畷市'
            ELSE municipality_name
        END AS municipality_name,
        surface_type_code,
        section_type_code,
        section_code,
        list_transform(
            string_split(section_code, ','),
            c -> {{ metropolitan_section_name('c') }}
        ) AS section_names,
        note,
        geom
    FROM {{ ref('raw_metropolitan_area') }}
    WHERE geom IS NOT NULL
)

SELECT
    metropolitan_area_code,
    lg_code,
    prefecture_name,
    district_name,
    municipality_name,
    surface_type_code,
    section_type_code,
    section_code,
    CASE
        WHEN list_count(section_names) = len(section_names)
            THEN array_to_string(section_names, '、')
    END AS section_name,
    note,
    -- 面だけを取り出して型を揃える（ST_MakeValid が線分や点を含む
    -- GEOMETRYCOLLECTION を返すことがある）
    ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(geom)), 3) AS geometry
FROM fixed
