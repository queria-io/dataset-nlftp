SELECT
    d.admin_code,
    left(d.admin_code, 2) AS prefecture_code,
    {{ prefecture_name_from_code('left(d.admin_code, 2)') }} AS prefecture_name,
    -- 原典に市区町村名の属性が無いので、利用条件一覧の自治体名を使う
    t.municipality_name,
    -- 学校コードは英字1桁 + 数字12桁。原典には「閉校」のようにコードでない値も
    -- 混じるので、結合キーとして使えない値は NULL にする
    CASE WHEN regexp_matches(d.school_code, '^[A-Z][0-9]{12}$') THEN d.school_code END
        AS school_code,
    d.school_name,
    d.establisher,
    d.address,
    -- 一部のポリゴンは ST_MakeValid で線分・点を含む GEOMETRYCOLLECTION になるため、
    -- 面だけを取り出して型を揃える（面積は変わらない）
    ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(d.geom)), 3) AS geometry
FROM {{ ref('raw_elementary_school_district') }} AS d
LEFT JOIN {{ ref('raw_school_district_terms') }} AS t
    ON d.admin_code = t.admin_code
WHERE d.geom IS NOT NULL
