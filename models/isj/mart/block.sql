{{ config(materialized='table', tags=['isj']) }}

-- 原典に市区町村コードが無いので、ABR の市区町村マスタと都道府県名・市区町村名で
-- 突き合わせて 6 桁の lg_code を付ける。原典の市区町村名は郡名を含む町村
-- （西多摩郡瑞穂町）と含まない町村があり、政令市は市名と区名を続けて書く
WITH names AS (
    SELECT lg_code, pref, coalesce(county, '') || city || coalesce(ward, '') AS name
    FROM {{ ref('raw_mt_city') }}
    WHERE ablt_date IS NULL AND city IS NOT NULL
    UNION
    SELECT lg_code, pref, city || coalesce(ward, '') AS name
    FROM {{ ref('raw_mt_city') }}
    WHERE ablt_date IS NULL AND city IS NOT NULL AND county IS NOT NULL
),
-- 郡名を落とした名前は同じ道府県の中で重なることがある（北海道の古宇郡泊村と
-- 国後郡泊村がどちらも「泊村」）。重なる名前で突き合わせると街区の行が増えるので、
-- 道府県の中で 1 つに決まる名前だけを使う
cities AS (
    SELECT lg_code, pref, name
    FROM names
    QUALIFY count(*) OVER (PARTITION BY pref, name) = 1
)
SELECT
    c.lg_code,
    b.prefecture_name,
    b.city_name,
    b.oaza_chome_name,
    b.koaza_name,
    b.block_number,
    b.plane_rectangular_zone,
    b.x,
    b.y,
    b.lat,
    b.lng,
    b.is_residential_address,
    b.is_representative,
    b.before_update_flag,
    b.after_update_flag,
    ST_Point(b.lng, b.lat) AS geometry
FROM {{ ref('stg_block') }} b
LEFT JOIN cities c ON c.pref = b.prefecture_name AND c.name = b.city_name
-- 履歴フラグの 3 は削除された街区符号・地番。原典の利用上の注意に従って除く
WHERE b.before_update_flag IS DISTINCT FROM '3'
    AND b.after_update_flag IS DISTINCT FROM '3'
ORDER BY c.lg_code, b.oaza_chome_name, b.koaza_name, b.block_number
