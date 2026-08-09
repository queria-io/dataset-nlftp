"""国土数値情報 S12 駅別乗降客数のダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から全国版の駅別乗降客数データ
（駅の軌道区間ラインに乗降客数を付与した Shapefile）をダウンロードし展開する。
zip には Shift-JIS 版と UTF-8 版が同梱されるため、文字化けを避けて UTF-8 版のみを取り出す。

データソース: 駅別乗降客数データ（2024年度版・2011年度〜2024年度の乗降客数を収録）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-2024.html
"""

import logging
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

URL = "https://nlftp.mlit.go.jp/ksj/gml/data/S12/S12-25/S12-25_GML.zip"

# 駅別乗降客数レイヤと Shapefile を構成する拡張子
_LAYER = "S12-25_NumberOfPassengers"
_EXTS = (".shp", ".shx", ".dbf", ".prj")

EXPECTED_SHP = f"{_LAYER}.shp"


def download_station_passenger(dest_dir: str) -> None:
    """全国版の駅別乗降客数データをダウンロードし展開する。

    zip 内の UTF-8 版 Shapefile のみをフラットに配置する。
    既にダウンロード済みの場合はスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    if (dest / EXPECTED_SHP).exists():
        logger.info(f"  skip (already exists: {dest / EXPECTED_SHP})")
        return

    zip_path = dest / "S12-25_GML.zip"

    logger.info("  downloading S12 station passenger data...")
    req = Request(URL, headers={"User-Agent": "dataset-nlftp"})
    with urlopen(req) as resp, open(zip_path, "wb") as f:
        f.write(resp.read())

    with zipfile.ZipFile(zip_path) as zf:
        for ext in _EXTS:
            member = f"S12-25_GML/UTF-8/{_LAYER}{ext}"
            with zf.open(member) as src, open(dest / f"{_LAYER}{ext}", "wb") as dst:
                dst.write(src.read())

    zip_path.unlink()
    logger.info(f"  station passenger data ready in {dest}")
