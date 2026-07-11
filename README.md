# dataset-nlftp

国土数値情報（nlftp.mlit.go.jp）の行政区域・将来推計人口・鉄道・医療機関・学校・福祉施設の GIS データを DuckLake カタログ化したデータセット。

## データ出典

国土交通省「国土数値情報ダウンロードサイト」が公開する以下のデータを使用する。

行政区域データ（N03、令和7年版 / 世界測地系）から全国の都道府県・市区町村の境界ポリゴンを収録する。座標参照系は EPSG:4612（JGD2011）。

- 行政区域データ（N03-2025）: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2025.html

将来推計人口は「1kmメッシュ別将来推計人口データ（R6国政局推計）」を使用する。推計値は総務省「令和2年国勢調査」と国立社会保障・人口問題研究所「日本の地域別将来推計人口（令和5年推計）」に基づき、2020〜2070年の5年ごとの値を収録する。メッシュポリゴンの座標参照系は EPSG:6668（JGD2011）。

- 1kmメッシュ別将来推計人口（R6国政局推計）: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-mesh1000r6.html

鉄道データは「鉄道データ（N02、令和6年版）」を使用する。全国の鉄道路線・駅を収録する。座標参照系は EPSG:6668（JGD2011）。

- 鉄道データ（N02-2024）: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2024.html

医療機関データは「医療機関データ（P04、第3.0版 / 令和2年）」を使用する。全国の病院・診療所・歯科診療所の位置・診療科目・病床数・開設者分類を収録する。座標参照系は EPSG:6668（JGD2011）。

- 医療機関データ（P04-v3.0）: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P04-v3_0.html

学校データは「学校データ（P29、第2.0版 / 令和3年）」を使用する。全国の小学校・中学校・高等学校・大学・幼稚園・特別支援学校等の位置・学校分類・管理者を収録する。座標参照系は EPSG:6668（JGD2011）。

- 学校データ（P29-v2.0）: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P29-v2_0.html

福祉施設データは「福祉施設データ（P14、第2.1版 / 令和3年度）」を使用する。全国の保護施設・老人福祉施設・障害者支援施設・身体障害者社会参加支援施設・児童福祉施設・母子父子福祉施設等の位置・分類（大／中／小）・管理者を収録する。全国版が無く都道府県別に配布されるため47都道府県分を統合する。座標参照系は EPSG:6668（JGD2011）。一部の都道府県・市区町村は利用規約と異なる利用条件が付されているため、利用時は提供元の利用制限を確認すること。

- 福祉施設データ（P14-v2.1）: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P14-v2_1.html

政令指定都市の区から市へのコード対応には、デジタル庁「アドレス・ベース・レジストリ（市区町村マスタデータ）」を加工して利用する。

- アドレス・ベース・レジストリ: https://dataset.address-br.digital.go.jp/

## テーブル: prefecture

都道府県の行政区域境界ポリゴン。N03（令和7年）の行政区域データを都道府県単位で集約したもの。

- prefecture_code: 都道府県コード（2桁）
- prefecture_name: 都道府県名
- geometry: 境界ポリゴン（EPSG:4612 / JGD2011）

## テーブル: municipality

市区町村の行政区域境界ポリゴン。N03（令和7年）の行政区域データを市区町村単位で集約したもの。同一自治体の飛び地等は ST_Union_Agg で統合済み。政令指定都市は区単位で収録され、行政区名を ward_name に持つ。

- lg_code: 全国地方公共団体コード（5桁、都道府県2桁 + 市区町村3桁）
- prefecture_code: 都道府県コード（2桁）
- prefecture_name: 都道府県名
- county_name: 郡名
- city_name: 市区町村名
- ward_name: 行政区名（政令指定都市のみ。他は NULL）
- geometry: 境界ポリゴン（EPSG:4612 / JGD2011）

## テーブル: designated_city

市区町村境界（政令指定都市の区を市レベルに統合）。municipality モデルから政令指定都市の区を ST_Union_Agg で結合し、市単位の境界として出力する。区コードから市コードへのマッピングは、デジタル庁「アドレス・ベース・レジストリ（市区町村マスタデータ）」を加工して作成。東京23区（特別区）は独立した地方公共団体のため統合しない。

- lg_code: 全国地方公共団体コード（5桁、政令指定都市は市レベルのコード）
- prefecture_code: 都道府県コード
- prefecture_name: 都道府県名
- county_name: 郡名
- city_name: 市区町村名
- geometry: 境界ポリゴン（EPSG:4612 / JGD2011）

## テーブル: future_population_municipality

市区町村別の将来推計人口（2020〜2070年、5年ごと）。1kmメッシュ別将来推計人口を市区町村コード（SHICODE）で集計したもの。複数市区町村にまたがるメッシュの人口は該当市区町村へ均等按分して集計する。政令指定都市は区単位のコードで収録される。

- city_code: 市区町村コード（5桁。政令指定都市は区単位）
- prefecture_code: 都道府県コード（2桁）
- prefecture_name / county_name / city_name / ward_name: 都道府県名・郡名・市区町村名・行政区名（行政区名は政令指定都市のみ、他は NULL）
- population_2020 〜 population_2070: 推計年次別の総人口（人、2020〜2070年の5年ごと）
- growth_rate_2025_2035 / growth_rate_2025_2050: 人口増減率（%。2025年比）
- elderly_ratio_2025 / elderly_ratio_2050: 高齢化率（65歳以上人口の割合、%）

メッシュの SHICODE は令和2年国勢調査時点のコードのため、その後に再編された一部の自治体（浜松市の旧行政区など）や福島県浜通りの特別集計コード（07999）では名称が NULL になる。

## テーブル: future_population_mesh

1kmメッシュ単位の将来推計人口。地図ヒートマップ用。

- mesh_id: メッシュコード（基準地域メッシュ、1km四方）
- city_code: 市区町村コード（複数市区町村にまたがるメッシュは "_" 連結）
- population_2025 / population_2035 / population_2050: 推計年次別の総人口（人）
- growth_rate_2025_2050: 人口増減率（%。2025年比）
- elderly_ratio_2025 / elderly_ratio_2050: 高齢化率（%）
- geometry: メッシュポリゴン（EPSG:6668 / JGD2011）

## テーブル: railway_line

鉄道路線（路線名・運営会社・鉄道区分単位）のラインジオメトリ。N02（令和6年）の路線区間を路線単位に ST_Union_Agg で集約したもの。

- railway_class_code: 鉄道区分コード（N02_001。普通鉄道JR=11、普通鉄道=12、軌道=21 など）
- railway_class: 鉄道区分
- operator_type_code: 事業者種別コード（N02_002。JRの新幹線=1、JR在来線=2、公営鉄道=3、民営鉄道=4、第三セクター=5）
- operator_type: 事業者種別
- line_name: 路線名
- operator: 運営会社
- geometry: 路線ライン（EPSG:6668 / JGD2011）

## テーブル: station

駅の代表点（ポイント）。N02（令和6年）の駅データ。駅は元データでは軌道区間のラインで表現されるため、その重心を代表点とした。同一駅が複数路線に属する場合は路線ごとに行が分かれる。

- railway_class_code: 鉄道区分コード（N02_001）
- railway_class: 鉄道区分
- operator_type_code: 事業者種別コード（N02_002）
- operator_type: 事業者種別
- line_name: 路線名
- operator: 運営会社
- station_name: 駅名
- station_code: 駅コード（N02_005c。駅を一意に識別する番号）
- station_group_code: 駅グループコード（N02_005g。乗換可能な同一駅グループを束ねるコード）
- geometry: 駅ポイント（EPSG:6668 / JGD2011。軌道区間ラインの重心）

## テーブル: medical_institution

医療機関の位置（ポイント）。P04（第3.0版・令和2年）の医療機関データ。全国の病院・診療所・歯科診療所の名称・所在地・診療科目・病床数・開設者分類を収録する。

- medical_class_code: 医療機関分類コード（P04_001。病院=1、診療所=2、歯科診療所=3）
- medical_class: 医療機関分類
- institution_name: 施設名称
- address: 所在地
- departments: 診療科目（全角空白区切り）
- establisher_type_code: 開設者分類コード（P04_007。国=1、公的医療機関=2、社会保険関係団体=3、医療法人=4、個人=5、その他=6、分類対象外=9。病院のみ分類対象）
- establisher_type: 開設者分類
- bed_count: 病床数（P04_008。当該施設が有する病床総数）
- emergency_hospital: 救急告示病院（P04_009。指定あり／指定なし）
- disaster_base_hospital: 災害拠点病院（P04_010。基幹災害拠点病院／地域災害拠点病院／指定なし）
- geometry: 医療機関ポイント（EPSG:6668 / JGD2011）

## テーブル: school

学校の位置（ポイント）。P29（第2.0版・令和3年）の学校データ。全国の小学校・中学校・高等学校・大学・幼稚園・特別支援学校・認定こども園・専修学校等の名称・所在地・学校分類・管理者を収録する。行政区域コードで人口・統計データと結合できる。

- admin_code: 行政区域コード（P29_001。都道府県コードと市区町村コードからなる）
- school_code: 学校コード（P29_002。全国の学校に設定された固有コード）
- school_class_code: 学校分類コード（P29_003。小学校=16001、中学校=16002、中等教育学校=16003、高等学校=16004、高等専門学校=16005、短期大学=16006、大学=16007、幼稚園=16011、特別支援学校=16012、認定こども園=16013、義務教育学校=16014、各種学校=16015、専修学校=16016）
- school_class: 学校分類
- school_name: 名称
- address: 所在地（P29_005。市区町村名を省いた所在地）
- administrator_code: 管理者コード（P29_006。その他=0、国=1、都道府県=2、市区町村=3、民間=4）
- administrator: 管理者
- school_status_code: 休校区分コード（P29_007。調査なし=0、開校中=1、休校中=2）
- school_status: 休校区分
- geometry: 学校ポイント（EPSG:6668 / JGD2011）

## テーブル: welfare

福祉施設の位置（ポイント）。P14（第2.1版・令和3年度）の福祉施設データ。全国の保護施設・老人福祉施設・障害者支援施設・身体障害者社会参加支援施設・児童福祉施設・母子父子福祉施設等の名称・所在地・分類（大／中／小）・管理者を収録する。行政区域コードで人口・統計データと結合できる。

- prefecture: 都道府県名（P14_001）
- city: 市区町村名（P14_002）
- admin_code: 行政区域コード（P14_003）
- address: 所在地（P14_004。市区町村名を省いた所在地）
- major_class_code: 福祉施設大分類コード（P14_005。保護施設=01、老人福祉施設=02、障害者支援施設等=03、身体障害者社会参加支援施設=04、児童福祉施設等=05、母子・父子福祉施設=06、その他の社会福祉施設等=99）
- major_class: 福祉施設大分類
- middle_class_code: 福祉施設中分類コード（P14_006）
- middle_class: 福祉施設中分類
- minor_class_code: 福祉施設小分類コード（P14_007）
- minor_class: 福祉施設小分類（公式コードリストで名称が定義されない中間ノードは NULL）
- institution_name: 名称（P14_008）
- administrator_code: 管理者コード（P14_009。その他=0、国=1、都道府県=2、市区町村=3、民間=4、法人=5、不明=9。製品仕様書 第2.1版の定義に従う）
- administrator: 管理者
- position_accuracy_code: 位置正確度コード（P14_010。位置特定=1、小字・街区レベル=2、大字・町丁目レベル=3、市区町村レベル=4、都道府県レベル=5。2〜5 は代表点）
- position_accuracy: 位置正確度
- geometry: 福祉施設ポイント（EPSG:6668 / JGD2011）

### データ更新手順

1. 行政区域データ（N03）はパイプライン実行時に N03-2025 の全国版 GML を自動ダウンロードする。
2. 市区町村マスタ（ABR）はアドレス・ベース・レジストリのサイトから最新の zip をダウンロードし、`data/mt_city/mt_city_all.csv.zip` に配置してコミットする。
3. 将来推計人口（1kmメッシュ）はパイプライン実行時に全国版 Shapefile を自動ダウンロードする。
4. 鉄道データ（N02）はパイプライン実行時に全国版 Shapefile を自動ダウンロードする。
5. 医療機関データ（P04）はパイプライン実行時に全国版 GeoJSON を自動ダウンロードする。
6. 学校データ（P29）はパイプライン実行時に全国版 GeoJSON を自動ダウンロードする。
7. 福祉施設データ（P14）はパイプライン実行時に47都道府県分の GeoJSON を自動ダウンロードし統合する。
8. `bash scripts/build.sh local` でビルドする。

## クレジット

本データセットは以下の出典データを加工して作成している。

- 「国土数値情報（行政区域データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2025.html）
- 「国土数値情報（1kmメッシュ別将来推計人口データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-mesh1000r6.html）
- 「国土数値情報（鉄道データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2024.html）
- 「国土数値情報（医療機関データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P04-v3_0.html）
- 「国土数値情報（学校データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P29-v2_0.html）
- 「国土数値情報（福祉施設データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P14-v2_1.html）
- 「アドレス・ベース・レジストリ（市区町村マスタデータ）」（デジタル庁）（https://dataset.address-br.digital.go.jp/）

## ライセンス

国土数値情報の利用約款および政府標準利用規約（第2.0版）に従う。出典データは加工して利用している。

- 国土数値情報 利用約款: https://nlftp.mlit.go.jp/ksj/other/agreement.html
