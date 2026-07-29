"""国土数値情報 P11 バス停留所・N07 バスルートのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から全国版のバス停留所（ポイント）と
バスルート（ライン）をダウンロードし展開する。zip には Shift-JIS の Shapefile と
UTF-8 の GeoJSON が同梱されるため、文字化けを避けて UTF-8 版の GeoJSON のみを取り出す。

いずれも令和4年度（2022年度）版を使う。平成22年度の P11 第2.0版と平成23年度の N07 は
使用許諾条件が「非商用」で再配布できないため使わない。

データソース:
  バス停留所データ（第3.0版・令和4年度）
  https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P11-v3_0.html
  バスルートデータ（令和4年度）
  https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N07-2022.html
"""

import logging
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

BUS_STOP_URL = "https://nlftp.mlit.go.jp/ksj/gml/data/P11/P11-22/P11-22_SHP.zip"
BUS_ROUTE_URL = "https://nlftp.mlit.go.jp/ksj/gml/data/N07/N07-22/N07-22_SHP.zip"

# バス停留所は全国版 zip の中に都道府県別 zip が入れ子で入っている
PREFECTURE_CODES = [f"{code:02d}" for code in range(1, 48)]

# バスルートは全国 1 ファイル
BUS_ROUTE_MEMBER = "N07-22_SHP/N07-22.geojson"
BUS_ROUTE_GEOJSON = "N07-22.geojson"


def _download(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "dataset-nlftp"})
    with urlopen(req) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def _download_bus_stop(dest: Path) -> None:
    """バス停留所（P11・都道府県別）の GeoJSON を展開する。"""
    if all((dest / f"P11-22_{code}.geojson").exists() for code in PREFECTURE_CODES):
        logger.info("  skip bus stop (already exists)")
        return

    zip_path = dest / "P11-22_SHP.zip"
    logger.info("  downloading P11 bus stop data...")
    _download(BUS_STOP_URL, zip_path)

    with zipfile.ZipFile(zip_path) as outer:
        for code in PREFECTURE_CODES:
            member = f"P11-22_{code}_GML.zip"
            with outer.open(member) as raw:
                with zipfile.ZipFile(raw) as inner:
                    name = f"P11-22_{code}/P11-22_{code}.geojson"
                    with (
                        inner.open(name) as src,
                        open(dest / f"P11-22_{code}.geojson", "wb") as dst,
                    ):
                        dst.write(src.read())

    zip_path.unlink()


def _download_bus_route(dest: Path) -> None:
    """バスルート（N07・全国版）の GeoJSON を展開する。"""
    if (dest / BUS_ROUTE_GEOJSON).exists():
        logger.info("  skip bus route (already exists)")
        return

    zip_path = dest / "N07-22_SHP.zip"
    logger.info("  downloading N07 bus route data...")
    _download(BUS_ROUTE_URL, zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        with (
            zf.open(BUS_ROUTE_MEMBER) as src,
            open(dest / BUS_ROUTE_GEOJSON, "wb") as dst,
        ):
            dst.write(src.read())

    zip_path.unlink()


def download_transit(dest_dir: str) -> None:
    """バス停留所とバスルートをダウンロードし展開する。

    既にダウンロード済みのものはスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    _download_bus_stop(dest)
    _download_bus_route(dest)

    logger.info(f"  transit data ready in {dest}")
