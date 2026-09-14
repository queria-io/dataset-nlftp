"""国土数値情報 P04 医療機関データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から全国版の医療機関データ
（病院・診療所・歯科診療所のポイント）をダウンロードし展開する。zip には
Shift-JIS の Shapefile と UTF-8 の GeoJSON が同梱されるため、文字化けを
避けて UTF-8 版の GeoJSON のみを取り出す。

データソース: 医療機関データ（第3.0版・令和2年）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P04-v3_0.html
"""

import logging
import zipfile
from pathlib import Path

from pipelines.download import download

logger = logging.getLogger("pipelines")

URL = "https://nlftp.mlit.go.jp/ksj/gml/data/P04/P04-20/P04-20_GML.zip"

# zip 内の UTF-8 GeoJSON（Shapefile の .dbf は Shift-JIS で文字化けするため使わない）
MEMBER = "P04-20_GML/P04-20.geojson"
EXPECTED_GEOJSON = "P04-20.geojson"


def download_medical(dest_dir: str) -> None:
    """全国版の医療機関データ（ポイント）をダウンロードし展開する。

    zip 内の UTF-8 版 GeoJSON のみをフラットに配置する。
    既にダウンロード済みの場合はスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    if (dest / EXPECTED_GEOJSON).exists():
        logger.info(f"  skip (already exists: {dest / EXPECTED_GEOJSON})")
        return

    zip_path = dest / "P04-20_GML.zip"

    logger.info("  downloading P04 medical institution data...")
    download(URL, zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(MEMBER) as src, open(dest / EXPECTED_GEOJSON, "wb") as dst:
            dst.write(src.read())

    zip_path.unlink()
    logger.info(f"  medical institution data ready in {dest}")
