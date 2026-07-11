"""国土数値情報データパイプライン。

1. administrative_boundary: 行政区域データ取得 (N03)
2. mt_city:                 市区町村マスタ取得 (ABR)
3. future_population:       将来推計人口メッシュ取得 (1kmメッシュ R6推計)
4. railway:                 鉄道データ取得 (N02 駅・路線)
5. medical:                 医療機関データ取得 (P04)
6. school:                  学校データ取得 (P29)
7. welfare:                 福祉施設データ取得 (P14)
8. dbt:                     dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.administrative_boundary import download_administrative_boundary
from pipelines.future_population import download_future_population
from pipelines.medical import download_medical
from pipelines.mt_city import extract_mt_city
from pipelines.railway import download_railway
from pipelines.school import download_school
from pipelines.welfare import download_welfare

logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()

    result = dbt.invoke(["deps"])
    if not result.success:
        raise SystemExit("dbt deps failed")

    result = dbt.invoke(["build"])
    if not result.success:
        raise SystemExit("dbt build failed")

    result = dbt.invoke(["docs", "generate"])
    if not result.success:
        raise SystemExit("dbt docs generate failed")


def main():
    # 1. 行政区域データ (国土数値情報 N03)
    logger.info("1/8: administrative_boundary (行政区域データ)")
    download_administrative_boundary("data/administrative_boundary")

    # 2. 市区町村マスタ (アドレス・ベース・レジストリ)
    logger.info("2/8: mt_city (市区町村マスタ)")
    extract_mt_city("data/mt_city")

    # 3. 将来推計人口メッシュ (国土数値情報 1kmメッシュ R6推計)
    logger.info("3/8: future_population (将来推計人口メッシュ)")
    download_future_population("data/future_population")

    # 4. 鉄道データ (国土数値情報 N02 駅・路線)
    logger.info("4/8: railway (鉄道データ)")
    download_railway("data/railway")

    # 5. 医療機関データ (国土数値情報 P04)
    logger.info("5/8: medical (医療機関データ)")
    download_medical("data/medical")

    # 6. 学校データ (国土数値情報 P29)
    logger.info("6/8: school (学校データ)")
    download_school("data/school")

    # 7. 福祉施設データ (国土数値情報 P14)
    logger.info("7/8: welfare (福祉施設データ)")
    download_welfare("data/welfare")

    # 8. dbt ビルド
    logger.info("8/8: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
