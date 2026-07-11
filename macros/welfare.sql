{#
  福祉施設データ（P14）のコード値を名称に変換するマクロ。

    - 福祉施設大分類（P14_005）: 福祉施設大分類コード
    - 福祉施設中分類（P14_006）: 福祉施設中分類コード
    - 福祉施設小分類（P14_007）: 福祉施設小分類コード
    - 管理者（P14_009）: 製品仕様書 第2.1版の行政コード定義
    - 位置正確度（P14_010）: 位置正確度コード

  分類コードの中間ノード（公式コードリストで名称が「－」のもの）は名称 NULL とする。
  管理者コードは Web のコードリスト（管理者コード 第2.0版）には「法人=5」が
  欠落しているため、製品仕様書 第2.1版（KS-PS-P14-v2_1.pdf）の定義を採用する。
#}
{% macro welfare_major_class_name(col) %}
  CASE {{ col }}
    WHEN '01' THEN '保護施設'
    WHEN '02' THEN '老人福祉施設'
    WHEN '03' THEN '障害者支援施設等'
    WHEN '04' THEN '身体障害者社会参加支援施設'
    WHEN '05' THEN '児童福祉施設等'
    WHEN '06' THEN '母子・父子福祉施設'
    WHEN '99' THEN 'その他の社会福祉施設等'
  END
{% endmacro %}

{% macro welfare_middle_class_name(col) %}
  CASE {{ col }}
    WHEN '0101' THEN '救護施設'
    WHEN '0102' THEN '更生施設'
    WHEN '0103' THEN '医療保護施設'
    WHEN '0104' THEN '授産施設（保護）'
    WHEN '0105' THEN '宿所提供施設'
    WHEN '0199' THEN 'その他'
    WHEN '0201' THEN '養護老人ホーム'
    WHEN '0202' THEN '軽費老人ホーム'
    WHEN '0203' THEN '老人福祉センター'
    WHEN '0204' THEN '老人デイサービスセンター'
    WHEN '0205' THEN '老人短期入所施設'
    WHEN '0206' THEN '老人（在宅）介護支援センター'
    WHEN '0207' THEN '高齢者生活福祉センター（生活支援ハウス）'
    WHEN '0299' THEN 'その他'
    WHEN '0301' THEN '障害者支援施設'
    WHEN '0302' THEN '地域活動支援センター'
    WHEN '0303' THEN '福祉ホーム'
    WHEN '0399' THEN 'その他'
    WHEN '0401' THEN '身体障害者福祉センター'
    WHEN '0402' THEN '障害者更生センター'
    WHEN '0403' THEN '補装具製作施設'
    WHEN '0404' THEN '盲導犬訓練施設'
    WHEN '0405' THEN '視聴覚障害者情報提供施設'
    WHEN '0499' THEN 'その他'
    WHEN '0501' THEN '助産施設'
    WHEN '0502' THEN '乳児院'
    WHEN '0503' THEN '母子生活支援施設'
    WHEN '0504' THEN '保育所等'
    WHEN '0505' THEN '地域型保育事業所'
    WHEN '0506' THEN '認可外保育施設'
    WHEN '0507' THEN '児童養護施設'
    WHEN '0508' THEN '障害児入所施設'
    WHEN '0509' THEN '児童発達支援センター'
    WHEN '0510' THEN '児童心理治療施設'
    WHEN '0511' THEN '児童自立支援施設'
    WHEN '0512' THEN '児童家庭支援センター'
    WHEN '0513' THEN '児童館'
    WHEN '0514' THEN '児童遊園'
    WHEN '0599' THEN 'その他'
    WHEN '0601' THEN '母子・父子福祉センター'
    WHEN '0602' THEN '母子・父子休養ホーム'
    WHEN '0699' THEN 'その他'
    WHEN '9901' THEN '無料低額宿泊所（宿所提供施設）'
    WHEN '9902' THEN '授産施設（その他）'
    WHEN '9903' THEN '盲人ホーム'
    WHEN '9904' THEN '無料低額診療施設'
    WHEN '9905' THEN '隣保館'
    WHEN '9906' THEN 'へき地保健福祉館'
    WHEN '9907' THEN '有料老人ホーム'
    WHEN '9908' THEN '老人憩の家'
    WHEN '9909' THEN '地域福祉センター'
    WHEN '9910' THEN '介護保険等の施設'
    WHEN '9911' THEN '障害者サービス施設'
    WHEN '9912' THEN '児童福祉サービス施設'
    WHEN '9913' THEN '相談所等の施設'
    WHEN '9999' THEN 'その他'
  END
{% endmacro %}

{% macro welfare_minor_class_name(col) %}
  CASE {{ col }}
    WHEN '020101' THEN '養護老人ホーム（一般）'
    WHEN '020102' THEN '養護老人ホーム（盲）'
    WHEN '020199' THEN 'その他'
    WHEN '020201' THEN '軽費老人ホーム A 型'
    WHEN '020202' THEN '軽費老人ホーム B 型'
    WHEN '020203' THEN '軽費老人ホーム（ケアハウス）'
    WHEN '020204' THEN '都市型軽費老人ホーム'
    WHEN '020299' THEN 'その他'
    WHEN '020301' THEN '老人福祉センター（特 A 型）'
    WHEN '020302' THEN '老人福祉センター（ A 型）'
    WHEN '020303' THEN '老人福祉センター（ B 型）'
    WHEN '020399' THEN 'その他'
    WHEN '040101' THEN '身体障害者福祉センター（ A 型）'
    WHEN '040102' THEN '身体障害者福祉センター（ B 型）'
    WHEN '040199' THEN 'その他'
    WHEN '040501' THEN '点字図書館'
    WHEN '040502' THEN '点字出版施設'
    WHEN '040503' THEN '聴覚障害者情報提供施設'
    WHEN '040599' THEN 'その他'
    WHEN '050401' THEN '保育所'
    WHEN '050402' THEN '幼保連携型認定こども園'
    WHEN '050403' THEN '保育所型認定こども園'
    WHEN '050404' THEN '幼稚園型認定こども園'
    WHEN '050405' THEN '地方裁量型認定こども園'
    WHEN '050406' THEN 'へき地保育所'
    WHEN '050499' THEN 'その他'
    WHEN '050501' THEN '小規模保育事業所 A 型'
    WHEN '050502' THEN '小規模保育事業所 B 型'
    WHEN '050503' THEN '小規模保育事業所 C 型'
    WHEN '050504' THEN '家庭的保育事業所（保育ママ）'
    WHEN '050505' THEN '居宅訪問型保育事業所'
    WHEN '050506' THEN '事業所内保育事業所'
    WHEN '050599' THEN 'その他'
    WHEN '050801' THEN '障害児入所施設（福祉型）'
    WHEN '050802' THEN '障害児入所施設（医療型）'
    WHEN '050899' THEN 'その他'
    WHEN '050901' THEN '児童発達支援センター（福祉型）'
    WHEN '050902' THEN '児童発達支援センター（医療型）'
    WHEN '050999' THEN 'その他'
    WHEN '051301' THEN '小型児童館'
    WHEN '051302' THEN '児童センター'
    WHEN '051303' THEN '大型児童館 A 型'
    WHEN '051304' THEN '大型児童館 B 型'
    WHEN '051305' THEN '大型児童館 C 型'
    WHEN '051306' THEN 'その他の児童館'
    WHEN '051399' THEN 'その他'
    WHEN '990701' THEN '有料老人ホーム（サービス付き高齢者向け住宅以外）'
    WHEN '990702' THEN '有料老人ホーム（サービス付き高齢者向け住宅であるもの）'
    WHEN '990799' THEN 'その他'
    WHEN '991001' THEN '特別養護老人ホーム'
    WHEN '991002' THEN '介護老人福祉施設'
    WHEN '991003' THEN '地域密着型老人介護福祉施設'
    WHEN '991004' THEN '介護老人保健施設'
    WHEN '991005' THEN '介護療養型医療施設'
    WHEN '991006' THEN '介護医療院'
    WHEN '991007' THEN 'その他の介護サービス施設'
    WHEN '991301' THEN '発達障害者支援センター'
    WHEN '991302' THEN '児童相談所'
    WHEN '991303' THEN '地域包括支援センター'
    WHEN '991304' THEN '婦人相談所'
    WHEN '991305' THEN '配偶者暴力相談支援センター'
    WHEN '991306' THEN 'その他の相談所・支援センター等'
  END
{% endmacro %}

{% macro welfare_administrator_name(col) %}
  CASE {{ col }}
    WHEN 0 THEN 'その他'
    WHEN 1 THEN '国'
    WHEN 2 THEN '都道府県'
    WHEN 3 THEN '市区町村'
    WHEN 4 THEN '民間'
    WHEN 5 THEN '法人'
    WHEN 9 THEN '不明'
  END
{% endmacro %}

{% macro welfare_position_accuracy_name(col) %}
  CASE {{ col }}
    WHEN 1 THEN '位置特定'
    WHEN 2 THEN '小字・街区レベル（代表点）'
    WHEN 3 THEN '大字・町丁目レベル（代表点）'
    WHEN 4 THEN '市区町村レベル（代表点）'
    WHEN 5 THEN '都道府県レベル（代表点）'
  END
{% endmacro %}
