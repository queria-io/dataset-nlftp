-- 砂防指定地の配布があるのは提供元が原典資料の提供を受けた都道府県だけで、
-- その一覧は都道府県別のデータ時点と一致する。データ時点の無い都道府県の行が
-- 混ざっていないことを確かめる。
SELECT DISTINCT a.prefecture_code
FROM {{ ref('sabo_designated_area') }} AS a
LEFT JOIN {{ ref('raw_sabo_datapoint') }} AS d
    ON a.prefecture_code = d.prefecture_code
WHERE COALESCE(d.as_of, '') = ''
