-- 地すべり防止区域は都道府県 × 所管省庁ごとに公開条件が異なる。都道府県だけでは
-- 絞り込めないので、所管省庁まで含めて「オープンデータにて公開」以外が
-- 混ざっていないことを確かめる。
SELECT DISTINCT z.prefecture_code, z.competent_agency
FROM {{ ref('landslide_prevention_zone') }} AS z
LEFT JOIN {{ ref('raw_landslide_prevention_terms') }} AS t
    ON z.prefecture_code = t.prefecture_code
    AND z.competent_agency = t.agency_name
WHERE t.disclosure IS DISTINCT FROM 'オープンデータにて公開'
