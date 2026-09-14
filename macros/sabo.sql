{#
  砂防指定地データ（A52）の告示年月日を日付に直すマクロ。

  告示年月日（A52_006）は文字列型で、提供元の表記がそろっていない。
  「昭和42年3月30日」のような和暦の年月日がほとんどだが、年だけのもの・
  番号らしき数字・複数の告示を並べたもの・空白も混ざる。ここでは和暦の
  年月日として完全に読めるものだけを日付にし、それ以外は NULL にする。
  元の表記は notice_date_text にそのまま残す。
#}
{% macro sabo_notice_date(col) %}
  {%- set text = "replace(trim(" ~ col ~ "), '元年', '1年')" -%}
  {%- set pattern = "'^(明治|大正|昭和|平成|令和)([0-9]{1,2})年([0-9]{1,2})月([0-9]{1,2})日$'" -%}
  TRY_CAST(
    CASE
      WHEN regexp_full_match({{ text }}, '(明治|大正|昭和|平成|令和)[0-9]{1,2}年[0-9]{1,2}月[0-9]{1,2}日')
      THEN printf(
        '%04d-%02d-%02d',
        CASE regexp_extract({{ text }}, '^(明治|大正|昭和|平成|令和)', 1)
          WHEN '明治' THEN 1867
          WHEN '大正' THEN 1911
          WHEN '昭和' THEN 1925
          WHEN '平成' THEN 1988
          WHEN '令和' THEN 2018
        END + CAST(regexp_extract({{ text }}, {{ pattern }}, 2) AS INTEGER),
        CAST(regexp_extract({{ text }}, {{ pattern }}, 3) AS INTEGER),
        CAST(regexp_extract({{ text }}, {{ pattern }}, 4) AS INTEGER)
      )
    END
    AS DATE)
{% endmacro %}
