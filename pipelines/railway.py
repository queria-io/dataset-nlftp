"""国土数値情報 N02 鉄道データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から全国版の鉄道データ
（駅・路線区間の Shapefile）をダウンロードし展開する。zip には Shift-JIS 版と
UTF-8 版が同梱されるため、文字化けを避けて UTF-8 版のみを取り出す。

データソース: 鉄道データ（令和6年）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2024.html
"""

import logging
import zipfile
from pathlib import Path

from pipelines.download import download

logger = logging.getLogger("pipelines")

URL = "https://nlftp.mlit.go.jp/ksj/gml/data/N02/N02-24/N02-24_GML.zip"

# 駅・路線レイヤと Shapefile を構成する拡張子
_LAYERS = ("N02-24_Station", "N02-24_RailroadSection")
_EXTS = (".shp", ".shx", ".dbf", ".prj")

EXPECTED_SHP = "N02-24_Station.shp"


def download_railway(dest_dir: str) -> None:
    """全国版の鉄道データ（駅・路線）をダウンロードし展開する。

    zip 内の UTF-8 版 Shapefile のみをフラットに配置する。
    既にダウンロード済みの場合はスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    if (dest / EXPECTED_SHP).exists():
        logger.info(f"  skip (already exists: {dest / EXPECTED_SHP})")
        return

    zip_path = dest / "N02-24_GML.zip"

    logger.info("  downloading N02 railway data...")
    download(URL, zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        for layer in _LAYERS:
            for ext in _EXTS:
                member = f"UTF-8/{layer}{ext}"
                with zf.open(member) as src, open(dest / f"{layer}{ext}", "wb") as dst:
                    dst.write(src.read())

    zip_path.unlink()
    logger.info(f"  railway data ready in {dest}")
