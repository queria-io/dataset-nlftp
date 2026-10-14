{#
  三大都市圏計画区域データ（A03）のコード値を名称に変換するマクロ。

    - 圏域: 配布ファイルの単位（ファイル名の接尾辞）
    - 陸水等区分（A03_005）: 列挙型（陸地・湖沼・湖沼内の島・海上）
    - 区域区分（A03_006）: 圏域ごとにコードの意味が違う
      （コードリスト SectionTypeCd_syuto_2025 / SectionTypeCd_cyubu / SectionTypeCd_kinki_2025）
    - 区域コード（A03_007）: 頭文字（S / C / K）で圏域が分かれるので、3 つの
      コードリストを 1 つにまとめても衝突しない
      （コードリスト SectionCd_syuto_2025 / SectionCd_cyubu / SectionCd_kinki_2025）。
      名称は「区域の種類.区域名」の形でコードリストの記載のまま
#}
{% macro metropolitan_area_name(col) %}
  CASE {{ col }}
    WHEN 'SYUTO' THEN '首都圏'
    WHEN 'CHUBU' THEN '中部圏'
    WHEN 'KINKI' THEN '近畿圏'
  END
{% endmacro %}

{% macro metropolitan_surface_type_name(col) %}
  CASE {{ col }}
    WHEN '1' THEN '陸地'
    WHEN '2' THEN '湖沼'
    WHEN '3' THEN '湖沼内の島'
    WHEN '4' THEN '海上'
  END
{% endmacro %}

{% macro metropolitan_section_type_name(area_col, col) %}
  CASE
    WHEN {{ col }} = '0' THEN '無指定'
    WHEN {{ area_col }} = 'SYUTO' THEN
      CASE {{ col }}
        WHEN '1' THEN '既成市街地'
        WHEN '2' THEN '近郊整備地帯（近郊緑地保全区域との複合無し）'
        WHEN '3' THEN '都市開発区域'
        WHEN '4' THEN '近郊緑地保全区域（全て近郊整備地帯内）'
      END
    WHEN {{ area_col }} = 'CHUBU' THEN
      CASE {{ col }}
        WHEN '1' THEN '都市整備区域（保全区域との重複無し）'
        WHEN '2' THEN '都市開発区域'
        WHEN '3' THEN '保全区域（都市整備区域との重複無し）'
        WHEN '4' THEN '保全区域、都市整備区域との重複区域'
      END
    WHEN {{ area_col }} = 'KINKI' THEN
      CASE {{ col }}
        WHEN '1' THEN '既成都市区域'
        WHEN '2' THEN '近郊整備区域'
        WHEN '3' THEN '都市開発区域'
        WHEN '4' THEN '保全区域（近郊緑地保全区域との重複無し）'
        WHEN '5' THEN '近郊緑地保全区域（全て保全区域内）'
      END
  END
{% endmacro %}

{% macro metropolitan_section_name(col) %}
  CASE {{ col }}
    WHEN 'S01' THEN '既成市街地'
    WHEN 'S02T' THEN '近郊整備区域.東京都'
    WHEN 'S02S' THEN '近郊整備区域.埼玉県'
    WHEN 'S02C' THEN '近郊整備区域.千葉県'
    WHEN 'S02K' THEN '近郊整備区域.神奈川県'
    WHEN 'S02I' THEN '近郊整備区域.茨城県'
    WHEN 'S03KF' THEN '都市開発区域.熊谷・深谷地区'
    WHEN 'S03KS' THEN '都市開発区域.古河・総和地区'
    WHEN 'S03I' THEN '都市開発区域.石岡地区'
    WHEN 'S03TU' THEN '都市開発区域.筑波地区'
    WHEN 'S03KO' THEN '都市開発区域.甲府地区'
    WHEN 'S03KA' THEN '都市開発区域.鹿島地区'
    WHEN 'S03MH' THEN '都市開発区域.水戸・日立地区'
    WHEN 'S03OT' THEN '都市開発区域.太田・館林地区'
    WHEN 'S03O' THEN '都市開発区域.大田原地区'
    WHEN 'S03C' THEN '都市開発区域.秩父地区'
    WHEN 'S03SU' THEN '都市開発区域.下館・結城地区'
    WHEN 'S03K' THEN '都市開発区域.桐生地区'
    WHEN 'S03U' THEN '都市開発区域.宇都宮地区'
    WHEN 'S03SA' THEN '都市開発区域.佐野・足利地区'
    WHEN 'S03TO' THEN '都市開発区域.栃木地区'
    WHEN 'S03OY' THEN '都市開発区域.小山地区'
    WHEN 'S03MT' THEN '都市開発区域.前橋・高崎地区'
    WHEN 'S03H' THEN '都市開発区域.本庄地区'
    WHEN 'S03TA' THEN '都市開発区域.土浦・阿見地区'
    WHEN 'S04T' THEN '近郊緑地保全区域.武山近郊緑地保全区域'
    WHEN 'S04KO' THEN '近郊緑地保全区域.衣笠・大楠山近郊緑地保全区域'
    WHEN 'S04ZH' THEN '近郊緑地保全区域.逗子・葉山近郊緑地保全区域'
    WHEN 'S04S' THEN '近郊緑地保全区域.相模原近郊緑地保全区域'
    WHEN 'S04TK' THEN '近郊緑地保全区域.多磨丘陵北部近郊緑地保全区域'
    WHEN 'S04TY' THEN '近郊緑地保全区域.滝山近郊緑地保全区域'
    WHEN 'S04SY' THEN '近郊緑地保全区域.狭山近郊緑地保全区域'
    WHEN 'S04A' THEN '近郊緑地保全区域.荒川近郊緑地保全区域'
    WHEN 'S04AG' THEN '近郊緑地保全区域.安行近郊緑地保全区域'
    WHEN 'S04HC' THEN '近郊緑地保全区域.東千葉近郊緑地保全区域'
    WHEN 'S04EK' THEN '近郊緑地保全区域.円海山・北鎌倉近郊緑地保全区域'
    WHEN 'S04U' THEN '近郊緑地保全区域.牛久沼近郊緑地保全区域'
    WHEN 'S04H' THEN '近郊緑地保全区域.平林寺近郊緑地保全区域'
    WHEN 'S04I' THEN '近郊緑地保全区域.入間近郊緑地保全区域'
    WHEN 'S04G' THEN '近郊緑地保全区域.行徳近郊緑地保全区域'
    WHEN 'S04KI' THEN '近郊緑地保全区域.剣崎・岩堂山近郊緑地保全区域'
    WHEN 'S04K' THEN '近郊緑地保全区域.君津近郊緑地保全区域'
    WHEN 'S04TS' THEN '近郊緑地保全区域.利根川・菅生沼近郊緑地保全区域'
    WHEN 'C01' THEN '都市整備区域'
    WHEN 'C02TT' THEN '都市開発区域.富山・高岡区域'
    WHEN 'C02KK' THEN '都市開発区域.金沢・小松区域'
    WHEN 'C02FS' THEN '都市開発区域.福井・坂井区域'
    WHEN 'C02NU' THEN '都市開発区域.長野・上田区域'
    WHEN 'C02ID' THEN '都市開発区域.伊那谷区域'
    WHEN 'C02G' THEN '都市開発区域.岐阜区域'
    WHEN 'C02T' THEN '都市開発区域.高山区域'
    WHEN 'C02HS' THEN '都市開発区域.東駿河湾区域'
    WHEN 'C02NS' THEN '都市開発区域.西駿河湾区域'
    WHEN 'C02E' THEN '都市開発区域.遠州区域'
    WHEN 'C02H' THEN '都市開発区域.東三河区域'
    WHEN 'C02IS' THEN '都市開発区域.伊勢区域'
    WHEN 'C02B' THEN '都市開発区域.琵琶湖東北部区域'
    WHEN 'C03CS' THEN '保全区域.中部山岳区域'
    WHEN 'C03HS' THEN '保全区域.白山区域'
    WHEN 'C03JK' THEN '保全区域.上信越高原区域'
    WHEN 'C03MA' THEN '保全区域.南アルプス区域'
    WHEN 'C03FI' THEN '保全区域.富士伊豆区域'
    WHEN 'C03IS' THEN '保全区域.伊勢志摩区域'
    WHEN 'C03NH' THEN '保全区域.能登半島区域'
    WHEN 'C03EK' THEN '保全区域.越前加賀海岸区域'
    WHEN 'C03YC' THEN '保全区域.八ヶ岳中信高原区域'
    WHEN 'C03HK' THEN '保全区域.飛騨木曽川区域'
    WHEN 'C03MW' THEN '保全区域.三河湾区域'
    WHEN 'C03S' THEN '保全区域.鈴鹿区域'
    WHEN 'C03TO' THEN '保全区域.天竜奥三河区域'
    WHEN 'C03CA' THEN '保全区域.中央アルプス区域'
    WHEN 'C03II' THEN '保全区域.揖斐伊吹区域'
    WHEN 'C03H' THEN '保全区域.浜名湖区域'
    WHEN 'C03AK' THEN '保全区域.愛知高原区域'
    WHEN 'C03AA' THEN '保全区域.赤目青山香肌峡区域'
    WHEN 'K01' THEN '既成都市区域'
    WHEN 'K02K' THEN '近郊整備区域.京都地区'
    WHEN 'K02O' THEN '近郊整備区域.大阪地区'
    WHEN 'K02H' THEN '近郊整備区域.兵庫地区'
    WHEN 'K02N' THEN '近郊整備区域.奈良地区'
    WHEN 'K03F' THEN '都市開発区域.福井敦賀区域'
    WHEN 'K03BT' THEN '都市開発区域.琵琶湖東部区域'
    WHEN 'K03K' THEN '都市開発区域.京都中丹区域'
    WHEN 'K03B' THEN '都市開発区域.播磨区域'
    WHEN 'K03W' THEN '都市開発区域.和歌山区域'
    WHEN 'K03I' THEN '都市開発区域.伊賀区域'
    WHEN 'K04E' THEN '保全区域.越前海岸区域'
    WHEN 'K04W' THEN '保全区域.若狭湾区域'
    WHEN 'K04SU' THEN '保全区域.鈴鹿区域'
    WHEN 'K04A' THEN '保全区域.赤目室生月瀬区域'
    WHEN 'K04IS' THEN '保全区域.伊勢志摩区域'
    WHEN 'K04YO' THEN '保全区域.吉野熊野区域'
    WHEN 'K04B' THEN '保全区域.琵琶湖区域'
    WHEN 'K04SA' THEN '保全区域.山陰海岸区域'
    WHEN 'K04K' THEN '保全区域.京都区域'
    WHEN 'K04HO' THEN '保全区域.北摂連山区域'
    WHEN 'K04KON' THEN '保全区域.金剛生駒区域'
    WHEN 'K04IZ' THEN '保全区域.和泉葛城区域'
    WHEN 'K04SE' THEN '保全区域.瀬戸内海区域'
    WHEN 'K04R' THEN '保全区域.六甲区域'
    WHEN 'K04HY' THEN '保全区域.氷ノ山区域'
    WHEN 'K04HE' THEN '保全区域.平城山の辺区域'
    WHEN 'K04YA' THEN '保全区域.矢田斑鳩区域'
    WHEN 'K04F' THEN '保全区域.藤原飛鳥区域'
    WHEN 'K04KOY' THEN '保全区域.高野竜神区域'
    WHEN 'K04SH' THEN '保全区域.白浜田辺区域'
    WHEN 'K04KA' THEN '保全区域.枯木灘海岸区域'
    WHEN 'K05KY' THEN '近郊緑地保全区域.京都近郊緑地保全区域'
    WHEN 'K05H' THEN '近郊緑地保全区域.北摂連山近郊緑地保全区域'
    WHEN 'K05KO' THEN '近郊緑地保全区域.金剛生駒近郊緑地保全区域'
    WHEN 'K05I' THEN '近郊緑地保全区域.和泉葛城近郊緑地保全区域'
    WHEN 'K05R' THEN '近郊緑地保全区域.六甲近郊緑地保全区域'
    WHEN 'K05Y' THEN '近郊緑地保全区域.矢田斑鳩近郊緑地保全区域'
  END
{% endmacro %}
