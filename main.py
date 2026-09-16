"""国土数値情報データパイプライン。

1. administrative_boundary: 行政区域データ取得 (N03)
2. mt_city:                 市区町村マスタ取得 (ABR)
3. future_population:       将来推計人口メッシュ取得 (1kmメッシュ R6推計)
4. future_population_500m:  将来推計人口メッシュ取得 (500mメッシュ R6推計)
5. railway:                 鉄道データ取得 (N02 駅・路線)
6. medical:                 医療機関データ取得 (P04)
7. school:                  学校データ取得 (P29)
8. transit:                 バス停留所・バスルート取得 (P11 / N07)
9. flood:                   洪水浸水想定区域データ取得 (A31a)
10. landuse:                土地利用細分メッシュ取得 (L03-b-u)
11. station_passenger:      駅別乗降客数取得 (S12)
12. welfare:                福祉施設データ取得 (P14)
13. zoning:                 用途地域データ取得 (A29)
14. school_district:        通学区域データ取得 (A27 小学校区 / A32 中学校区)
15. tsunami:                津波浸水想定データ取得 (A40)
16. landslide:              土砂災害警戒区域データ取得 (A33)
17. storm_surge:            高潮浸水想定区域データ取得 (A49)
18. medical_area:           医療圏データ取得 (A38)
19. public_facility:        市町村役場等及び公的集会施設データ取得 (P05)
20. did:                    人口集中地区データ取得 (A16)
21. pluvial_flood:          雨水出水（内水）浸水想定区域データ取得 (A51)
22. multi_stage_flood:      多段階浸水想定データ取得 (A53)
23. depopulated_area:       過疎地域データ取得 (A17)
24. steep_slope:            急傾斜地崩壊危険区域データ取得 (A47)
25. landslide_prevention:   地すべり防止区域データ取得 (A46)
26. sabo:                   砂防指定地データ取得 (A52)
27. disaster_risk_area:     災害危険区域データ取得 (A48)
28. dbt:                    dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.administrative_boundary import download_administrative_boundary
from pipelines.depopulated_area import download_depopulated_area
from pipelines.did import download_did
from pipelines.disaster_risk_area import download_disaster_risk_area
from pipelines.flood import download_flood, flood_skipped
from pipelines.future_population import (
    download_future_population,
    download_future_population_500m,
)
from pipelines.landslide import download_landslide
from pipelines.landslide_prevention import download_landslide_prevention
from pipelines.landuse import download_landuse
from pipelines.medical import download_medical
from pipelines.medical_area import download_medical_area
from pipelines.mt_city import extract_mt_city
from pipelines.multi_stage_flood import download_multi_stage_flood
from pipelines.pluvial_flood import download_pluvial_flood
from pipelines.public_facility import download_public_facility
from pipelines.railway import download_railway
from pipelines.sabo import download_sabo
from pipelines.school import download_school
from pipelines.school_district import download_school_district
from pipelines.station_passenger import download_station_passenger
from pipelines.steep_slope import download_steep_slope
from pipelines.storm_surge import download_storm_surge
from pipelines.transit import download_transit
from pipelines.tsunami import download_tsunami
from pipelines.welfare import download_welfare
from pipelines.zoning import download_zoning

logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()

    result = dbt.invoke(["deps"])
    if not result.success:
        raise SystemExit("dbt deps failed")

    # 洪水データスキップ時は flood タグのモデルを除外してビルドする
    # （カタログ上の既存テーブルはそのまま維持される）
    build_args = ["build"]
    if flood_skipped():
        build_args += ["--exclude", "tag:flood"]

    result = dbt.invoke(build_args)
    if not result.success:
        raise SystemExit("dbt build failed")

    result = dbt.invoke(["docs", "generate"])
    if not result.success:
        raise SystemExit("dbt docs generate failed")


def main():
    # 1. 行政区域データ (国土数値情報 N03)
    logger.info("1/28: administrative_boundary (行政区域データ)")
    download_administrative_boundary("data/administrative_boundary")

    # 2. 市区町村マスタ (アドレス・ベース・レジストリ)
    logger.info("2/28: mt_city (市区町村マスタ)")
    extract_mt_city("data/mt_city")

    # 3. 将来推計人口メッシュ (国土数値情報 1kmメッシュ R6推計)
    logger.info("3/28: future_population (将来推計人口メッシュ)")
    download_future_population("data/future_population")

    # 4. 将来推計人口メッシュ (国土数値情報 500mメッシュ R6推計)
    logger.info("4/28: future_population_500m (将来推計人口メッシュ 500m)")
    download_future_population_500m("data/future_population_500m")

    # 5. 鉄道データ (国土数値情報 N02 駅・路線)
    logger.info("5/28: railway (鉄道データ)")
    download_railway("data/railway")

    # 6. 医療機関データ (国土数値情報 P04)
    logger.info("6/28: medical (医療機関データ)")
    download_medical("data/medical")

    # 7. 学校データ (国土数値情報 P29)
    logger.info("7/28: school (学校データ)")
    download_school("data/school")

    # 8. バス停留所・バスルート (国土数値情報 P11 / N07)
    logger.info("8/28: transit (バス停留所・バスルート)")
    download_transit("data/transit")

    # 9. 洪水浸水想定区域データ (国土数値情報 A31a)
    logger.info("9/28: flood (洪水浸水想定区域データ)")
    download_flood("data/flood")

    # 10. 都市地域土地利用細分メッシュ (国土数値情報 L03-b-u)
    logger.info("10/28: landuse (土地利用細分メッシュ)")
    download_landuse("data/landuse")

    # 11. 駅別乗降客数 (国土数値情報 S12)
    logger.info("11/28: station_passenger (駅別乗降客数)")
    download_station_passenger("data/station_passenger")

    # 12. 福祉施設データ (国土数値情報 P14)
    logger.info("12/28: welfare (福祉施設データ)")
    download_welfare("data/welfare")

    # 13. 用途地域データ (国土数値情報 A29)
    logger.info("13/28: zoning (用途地域データ)")
    download_zoning("data/zoning")

    # 14. 通学区域データ (国土数値情報 A27 小学校区 / A32 中学校区)
    logger.info("14/28: school_district (通学区域データ)")
    download_school_district("data/school_district")

    # 15. 津波浸水想定データ (国土数値情報 A40)
    logger.info("15/28: tsunami (津波浸水想定データ)")
    download_tsunami("data/tsunami")

    # 16. 土砂災害警戒区域データ (国土数値情報 A33)
    logger.info("16/28: landslide (土砂災害警戒区域データ)")
    download_landslide("data/landslide")

    # 17. 高潮浸水想定区域データ (国土数値情報 A49)
    logger.info("17/28: storm_surge (高潮浸水想定区域データ)")
    download_storm_surge("data/storm_surge")

    # 18. 医療圏データ (国土数値情報 A38)
    logger.info("18/28: medical_area (医療圏データ)")
    download_medical_area("data/medical_area")

    # 19. 市町村役場等及び公的集会施設データ (国土数値情報 P05)
    logger.info("19/28: public_facility (市町村役場等及び公的集会施設データ)")
    download_public_facility("data/public_facility")

    # 20. 人口集中地区データ (国土数値情報 A16)
    logger.info("20/28: did (人口集中地区データ)")
    download_did("data/did")

    # 21. 雨水出水（内水）浸水想定区域データ (国土数値情報 A51)
    logger.info("21/28: pluvial_flood (雨水出水（内水）浸水想定区域データ)")
    download_pluvial_flood("data/pluvial_flood")

    # 22. 多段階浸水想定データ (国土数値情報 A53)
    logger.info("22/28: multi_stage_flood (多段階浸水想定データ)")
    download_multi_stage_flood("data/multi_stage_flood")

    # 23. 過疎地域データ (国土数値情報 A17)
    logger.info("23/28: depopulated_area (過疎地域データ)")
    download_depopulated_area("data/depopulated_area")

    # 24. 急傾斜地崩壊危険区域データ (国土数値情報 A47)
    logger.info("24/28: steep_slope (急傾斜地崩壊危険区域データ)")
    download_steep_slope("data/steep_slope")

    # 25. 地すべり防止区域データ (国土数値情報 A46)
    logger.info("25/28: landslide_prevention (地すべり防止区域データ)")
    download_landslide_prevention("data/landslide_prevention")

    # 26. 砂防指定地データ (国土数値情報 A52)
    logger.info("26/28: sabo (砂防指定地データ)")
    download_sabo("data/sabo")

    # 27. 災害危険区域データ (国土数値情報 A48)
    logger.info("27/28: disaster_risk_area (災害危険区域データ)")
    download_disaster_risk_area("data/disaster_risk_area")

    # 28. dbt ビルド
    logger.info("28/28: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
