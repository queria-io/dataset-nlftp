-- 原典は公示年月日の不明を 9999/1/1、指定面積の未記載を 0 で表す。そのまま残ると
-- 公示年の分布や面積の合計が静かに狂う。センチネルが NULL に直っていることを検査する。
SELECT prefecture_code, zone_name
FROM {{ ref('steep_slope_hazard_zone') }}
WHERE notice_date = DATE '9999-01-01' OR designated_area_ha = 0
