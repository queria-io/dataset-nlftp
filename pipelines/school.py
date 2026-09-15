"""国土数値情報 P29 学校データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から全国版の学校データ
（小学校・中学校・高等学校・大学・幼稚園等のポイント）をダウンロードし
展開する。zip には Shift-JIS の Shapefile と UTF-8 の GeoJSON が同梱される
ため、文字化けを避けて UTF-8 版の GeoJSON のみを取り出す。

データソース: 学校データ（第2.0版・令和3年）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P29-v2_0.html
"""

import logging
import zipfile
from pathlib import Path

from pipelines.download import download

logger = logging.getLogger("pipelines")

URL = "https://nlftp.mlit.go.jp/ksj/gml/data/P29/P29-21/P29-21_GML.zip"

# zip 内の UTF-8 GeoJSON（Shapefile の .dbf は Shift-JIS で文字化けするため使わない）
MEMBER = "P29-21.geojson"
EXPECTED_GEOJSON = "P29-21.geojson"


def download_school(dest_dir: str) -> None:
    """全国版の学校データ（ポイント）をダウンロードし展開する。

    zip 内の UTF-8 版 GeoJSON のみをフラットに配置する。
    既にダウンロード済みの場合はスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    if (dest / EXPECTED_GEOJSON).exists():
        logger.info(f"  skip (already exists: {dest / EXPECTED_GEOJSON})")
        return

    zip_path = dest / "P29-21_GML.zip"

    logger.info("  downloading P29 school data...")
    download(URL, zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(MEMBER) as src, open(dest / EXPECTED_GEOJSON, "wb") as dst:
            dst.write(src.read())

    zip_path.unlink()
    logger.info(f"  school data ready in {dest}")
