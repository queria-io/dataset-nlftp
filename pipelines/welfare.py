"""国土数値情報 P14 福祉施設データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から福祉施設データ（高齢者・
障害者・児童福祉施設等のポイント）をダウンロードし展開する。P14 は全国版が
無く都道府県別に配布されるため、47 都道府県分の zip を取得し、各 zip に同梱
される UTF-8 の GeoJSON を 1 つの FeatureCollection に統合する。zip には
Shift-JIS の Shapefile も含まれるが、文字化けを避けて GeoJSON のみを使う。

データソース: 福祉施設データ（第2.1版・令和3年度）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P14-v2_1.html
"""

import json
import logging
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

URL_TEMPLATE = "https://nlftp.mlit.go.jp/ksj/gml/data/P14/P14-21/P14-21_{pref:02d}_GML.zip"

# 都道府県コード 01〜47
PREF_CODES = range(1, 48)

# 統合後の GeoJSON（raw モデルが ST_Read で読む単一ファイル）
MERGED_GEOJSON = "P14-21.geojson"


def _download_prefecture(pref: int, dest: Path) -> Path:
    """1 県分の zip を取得し、同梱の UTF-8 GeoJSON を取り出してパスを返す。"""
    geojson_name = f"P14-21_{pref:02d}.geojson"
    geojson_path = dest / geojson_name
    if geojson_path.exists():
        return geojson_path

    zip_path = dest / f"P14-21_{pref:02d}_GML.zip"
    url = URL_TEMPLATE.format(pref=pref)
    req = Request(url, headers={"User-Agent": "dataset-nlftp"})
    with urlopen(req) as resp, open(zip_path, "wb") as f:
        f.write(resp.read())

    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(geojson_name) as src, open(geojson_path, "wb") as dst:
            dst.write(src.read())

    zip_path.unlink()
    return geojson_path


def download_welfare(dest_dir: str) -> None:
    """全国の福祉施設データ（ポイント）をダウンロードし 1 ファイルに統合する。

    47 都道府県分の GeoJSON を取得し、features を連結した単一の
    FeatureCollection を出力する。統合済みの場合はスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    if (dest / MERGED_GEOJSON).exists():
        logger.info(f"  skip (already exists: {dest / MERGED_GEOJSON})")
        return

    logger.info("  downloading P14 welfare data (47 prefectures)...")
    features: list[dict] = []
    crs = None
    for pref in PREF_CODES:
        geojson_path = _download_prefecture(pref, dest)
        with open(geojson_path, encoding="utf-8") as f:
            data = json.load(f)
        crs = crs or data.get("crs")
        features.extend(data["features"])

    merged = {"type": "FeatureCollection", "crs": crs, "features": features}
    with open(dest / MERGED_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False)

    logger.info(f"  welfare data ready in {dest} ({len(features)} features)")
