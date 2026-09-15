"""国土数値情報 メッシュ別将来推計人口（R6国政局推計）のダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から全国版の将来推計人口メッシュ
データ (Shapefile) をダウンロードし展開する。全国版 zip は 47 都道府県別 zip を
内包する入れ子構造のため、内側の zip も展開する。1km メッシュと 500m メッシュは
同じ推計・同じ属性体系で、粒度だけが違う。

データソース: 1kmメッシュ別将来推計人口データ（R6国政局推計、2025〜2070年）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-mesh1000r6.html
500mメッシュ別将来推計人口データ（R6国政局推計、2025〜2070年）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-mesh500r6.html
"""

import logging
import zipfile
from pathlib import Path

from pipelines.download import download

logger = logging.getLogger("pipelines")

URL = "https://nlftp.mlit.go.jp/ksj/gml/data/m1kr6/m1kr6-24/1km_mesh_2024_SHP.zip"
URL_500M = (
    "https://nlftp.mlit.go.jp/ksj/gml/data/m500r6/m500r6-24/500m_mesh_2024_SHP.zip"
)


def _download_mesh(dest_dir: str, url: str, prefix: str, label: str) -> None:
    """メッシュ別将来推計人口データをダウンロードし展開する。

    全国版 zip は都道府県別 zip を内包するため、内側の zip も展開する。
    既にダウンロード済みの場合はスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    # 展開後に生成される代表ファイル（存在すればダウンロード済みとみなす）
    expected_shp = f"{prefix}_SHP/{prefix}_01_SHP/{prefix}_01.shp"
    if (dest / expected_shp).exists():
        logger.info(f"  skip (already exists: {dest / expected_shp})")
        return

    zip_path = dest / f"{prefix}_SHP.zip"

    logger.info(f"  downloading {label} future population data...")
    download(url, zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    zip_path.unlink()

    # 都道府県別の入れ子 zip を展開する
    inner_dir = dest / f"{prefix}_SHP"
    for inner_zip in sorted(inner_dir.glob("*.zip")):
        with zipfile.ZipFile(inner_zip) as zf:
            zf.extractall(inner_dir)
        inner_zip.unlink()

    logger.info(f"  future population data ready in {dest}")


def download_future_population(dest_dir: str) -> None:
    """1kmメッシュ別将来推計人口データをダウンロードし展開する。"""
    _download_mesh(dest_dir, URL, "1km_mesh_2024", "1km mesh")


def download_future_population_500m(dest_dir: str) -> None:
    """500mメッシュ別将来推計人口データをダウンロードし展開する。"""
    _download_mesh(dest_dir, URL_500M, "500m_mesh_2024", "500m mesh")
