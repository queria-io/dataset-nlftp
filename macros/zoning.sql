{#
  用途地域データ（A29）のコード値を名称に変換するマクロ。

    - 用途地域分類コード（A29_004）: 用途地域の種類（コードリスト UseDistrictCd）
    - 都道府県コード: 都道府県名（原典の都道府県名は「鹿児島」「鹿児島県」のように
      表記が揺れるため、行政区域コードの上2桁から引き直す）
#}
{% macro prefecture_name_from_code(col) %}
  CASE {{ col }}
    WHEN '01' THEN '北海道'
    WHEN '02' THEN '青森県'
    WHEN '03' THEN '岩手県'
    WHEN '04' THEN '宮城県'
    WHEN '05' THEN '秋田県'
    WHEN '06' THEN '山形県'
    WHEN '07' THEN '福島県'
    WHEN '08' THEN '茨城県'
    WHEN '09' THEN '栃木県'
    WHEN '10' THEN '群馬県'
    WHEN '11' THEN '埼玉県'
    WHEN '12' THEN '千葉県'
    WHEN '13' THEN '東京都'
    WHEN '14' THEN '神奈川県'
    WHEN '15' THEN '新潟県'
    WHEN '16' THEN '富山県'
    WHEN '17' THEN '石川県'
    WHEN '18' THEN '福井県'
    WHEN '19' THEN '山梨県'
    WHEN '20' THEN '長野県'
    WHEN '21' THEN '岐阜県'
    WHEN '22' THEN '静岡県'
    WHEN '23' THEN '愛知県'
    WHEN '24' THEN '三重県'
    WHEN '25' THEN '滋賀県'
    WHEN '26' THEN '京都府'
    WHEN '27' THEN '大阪府'
    WHEN '28' THEN '兵庫県'
    WHEN '29' THEN '奈良県'
    WHEN '30' THEN '和歌山県'
    WHEN '31' THEN '鳥取県'
    WHEN '32' THEN '島根県'
    WHEN '33' THEN '岡山県'
    WHEN '34' THEN '広島県'
    WHEN '35' THEN '山口県'
    WHEN '36' THEN '徳島県'
    WHEN '37' THEN '香川県'
    WHEN '38' THEN '愛媛県'
    WHEN '39' THEN '高知県'
    WHEN '40' THEN '福岡県'
    WHEN '41' THEN '佐賀県'
    WHEN '42' THEN '長崎県'
    WHEN '43' THEN '熊本県'
    WHEN '44' THEN '大分県'
    WHEN '45' THEN '宮崎県'
    WHEN '46' THEN '鹿児島県'
    WHEN '47' THEN '沖縄県'
  END
{% endmacro %}
{% macro use_district_name(col) %}
  CASE {{ col }}
    WHEN 1 THEN '第一種低層住居専用地域'
    WHEN 2 THEN '第二種低層住居専用地域'
    WHEN 3 THEN '第一種中高層住居専用地域'
    WHEN 4 THEN '第二種中高層住居専用地域'
    WHEN 5 THEN '第一種住居地域'
    WHEN 6 THEN '第二種住居地域'
    WHEN 7 THEN '準住居地域'
    WHEN 8 THEN '近隣商業地域'
    WHEN 9 THEN '商業地域'
    WHEN 10 THEN '準工業地域'
    WHEN 11 THEN '工業地域'
    WHEN 12 THEN '工業専用地域'
    WHEN 21 THEN '田園住居地域'
    WHEN 99 THEN '不明'
  END
{% endmacro %}
