-- 原典は欠測値を -99999 で表す。前回人口・前回面積以外の列に欠測が現れると、
-- 人口や面積の合計が静かに狂う。数値列に -99999 が残っていないことを検査する。
SELECT did_code
FROM {{ ref('did') }}
WHERE -99999 IN (
    population, area_km2, previous_population, previous_area_km2,
    population_share_pct, area_share_pct,
    population_male, population_female, households
)
