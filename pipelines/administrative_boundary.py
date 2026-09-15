"""国土数値情報 N03 行政区域データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から全国版の行政区域データ (GML) をダウンロードし展開する。

データソース: 令和7年 行政区域データ（世界測地系）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2025.html
"""

import logging
import zipfile
from pathlib import Path

from pipelines.download import download

logger = logging.getLogger("pipelines")

URL = (
    "https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2025/N03-20250101_GML.zip"
)

EXPECTED_SHP = "N03-20250101.shp"


def download_administrative_boundary(dest_dir: str) -> None:
    """全国版の行政区域データをダウンロードし展開する。

    既にダウンロード済みの場合はスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    shp_path = dest / EXPECTED_SHP
    if shp_path.exists():
        logger.info(f"  skip (already exists: {shp_path})")
        return

    zip_path = dest / "N03.zip"

    logger.info("  downloading N03 administrative boundary data...")
    download(URL, zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)

    zip_path.unlink()
    logger.info(f"  administrative boundary data ready in {dest}")
