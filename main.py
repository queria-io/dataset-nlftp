"""国土数値情報データパイプライン。

1. administrative_boundary: 行政区域データ取得 (N03)
2. mt_city:                 市区町村マスタ取得 (ABR)
3. future_population:       将来推計人口メッシュ取得 (1kmメッシュ R6推計)
4. railway:                 鉄道データ取得 (N02 駅・路線)
5. medical:                 医療機関データ取得 (P04)
6. school:                  学校データ取得 (P29)
7. transit:                 バス停留所・バスルート取得 (P11 / N07)
8. flood:                   洪水浸水想定区域データ取得 (A31a)
9. landuse:                 土地利用細分メッシュ取得 (L03-b-u)
10. station_passenger:      駅別乗降客数取得 (S12)
11. zoning:                 用途地域データ取得 (A29)
12. dbt:                    dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.administrative_boundary import download_administrative_boundary
from pipelines.flood import download_flood, flood_skipped
from pipelines.future_population import download_future_population
from pipelines.landuse import download_landuse
from pipelines.medical import download_medical
from pipelines.mt_city import extract_mt_city
from pipelines.railway import download_railway
from pipelines.school import download_school
from pipelines.station_passenger import download_station_passenger
from pipelines.transit import download_transit
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
    logger.info("1/12: administrative_boundary (行政区域データ)")
    download_administrative_boundary("data/administrative_boundary")

    # 2. 市区町村マスタ (アドレス・ベース・レジストリ)
    logger.info("2/12: mt_city (市区町村マスタ)")
    extract_mt_city("data/mt_city")

    # 3. 将来推計人口メッシュ (国土数値情報 1kmメッシュ R6推計)
    logger.info("3/12: future_population (将来推計人口メッシュ)")
    download_future_population("data/future_population")

    # 4. 鉄道データ (国土数値情報 N02 駅・路線)
    logger.info("4/12: railway (鉄道データ)")
    download_railway("data/railway")

    # 5. 医療機関データ (国土数値情報 P04)
    logger.info("5/12: medical (医療機関データ)")
    download_medical("data/medical")

    # 6. 学校データ (国土数値情報 P29)
    logger.info("6/12: school (学校データ)")
    download_school("data/school")

    # 7. バス停留所・バスルート (国土数値情報 P11 / N07)
    logger.info("7/12: transit (バス停留所・バスルート)")
    download_transit("data/transit")

    # 8. 洪水浸水想定区域データ (国土数値情報 A31a)
    logger.info("8/12: flood (洪水浸水想定区域データ)")
    download_flood("data/flood")

    # 9. 都市地域土地利用細分メッシュ (国土数値情報 L03-b-u)
    logger.info("9/12: landuse (土地利用細分メッシュ)")
    download_landuse("data/landuse")

    # 10. 駅別乗降客数 (国土数値情報 S12)
    logger.info("10/12: station_passenger (駅別乗降客数)")
    download_station_passenger("data/station_passenger")

    # 11. 用途地域データ (国土数値情報 A29)
    logger.info("11/12: zoning (用途地域データ)")
    download_zoning("data/zoning")

    # 12. dbt ビルド
    logger.info("12/12: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
