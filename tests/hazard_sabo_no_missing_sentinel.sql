-- 原典は指定面積の未記載を 0、文字列の未記載を空白で表す。そのまま残ると
-- 面積の合計や未記載の数え方が静かに狂う。センチネルが NULL に直っている
-- ことを検査する。
SELECT prefecture_code, reference_number
FROM {{ ref('sabo_designated_area') }}
WHERE designated_area_ha = 0
    OR TRIM(COALESCE(river_name, 'x')) = ''
    OR TRIM(COALESCE(notice_date_text, 'x')) = ''
    OR TRIM(COALESCE(designation_method, 'x')) = ''
