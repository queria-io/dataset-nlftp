"""国土数値情報 A16 人口集中地区（DID）データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から人口集中地区の全国版 zip を
ダウンロードし、Parquet に変換して配置する。国勢調査の基本単位区のうち人口密度が
高い区域を市区町村ごとにまとめた区域（人口密度 4,000人/km² 以上の基本単位区が
互いに隣接して人口 5,000人以上になる地域）が原典で、総務省統計局「我が国の
人口集中地区」の区域を国土数値情報の行政区域に合わせて修正したもの。

配布ファイルの形式
------------------
zip には全国 1 ファイルの GeoJSON が入る。シェープファイルも同梱されるが、
GeoJSON の方が座標参照系の宣言（EPSG:6668）を持つのでこちらを使う。

1 行 = 1 人口集中地区で、地区が飛び地に分かれる分は 1 行のマルチポリゴンに
まとまっている。同じ市区町村に複数の地区が設定されることがあり、その場合は
人口の多い順に符号が振られた別々の行になる。

使用許諾条件は整備年度によって違い、1995年（平成7年）以降のものだけが商用可。
このパイプラインは2020年（令和2年）国勢調査に基づく A16-20 だけを取り込む。

データソース: 人口集中地区（A16、令和2年国勢調査）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A16-2020.html
"""

import logging
import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import duckdb

logger = logging.getLogger("pipelines")

PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A16-2020.html"

# 取り込む整備年度。A16-20 = 令和2年（2020年）国勢調査
FILE_STEM = "A16-20"

# 全国版 zip の中の GeoJSON（_00 が全国）
GEOJSON_NAME = f"{FILE_STEM}_00_DID.geojson"

# 使用許諾条件は整備年度で分かれる。1995年より前の版を商用可として扱わないよう、
# 記載が一字でも変わったら取り込みを続けない
LICENSE_TEXT = "1995年（平成7年）以降：商用可"


def _download(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "dataset-nlftp"})
    with urlopen(req) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f, 1024 * 1024)


def _fetch_page() -> str:
    """配布ページの HTML を取得する（HTML コメントは落とす）。"""
    req = Request(PAGE_URL, headers={"User-Agent": "dataset-nlftp"})
    with urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def _check_license(html: str) -> None:
    """1995年以降が商用可のままであることを確かめる。"""
    match = re.search(r"このデータの使用許諾条件(.{0,200})", html, flags=re.DOTALL)
    if match is None:
        raise SystemExit("license section not found on the distribution page")
    if LICENSE_TEXT not in re.sub(r"<[^>]+>", "", match.group(1)):
        raise SystemExit("license terms changed: commercial use statement not found")


def _find_url(html: str) -> str:
    """ダウンロード一覧から全国版 zip の URL を取り出す。

    一覧には1960年から5年ごとの過年度整備分と都道府県別の zip も並ぶ。
    取り込む年度の全国版だけを拾う。
    """
    for path in re.findall(r"DownLd\([^)]*'((?:\.\./)?data/A16/[^']+\.zip)'", html):
        if path.rsplit("/", 1)[-1] == f"{FILE_STEM}_GML.zip":
            return urljoin(PAGE_URL, path)
    raise SystemExit(f"{FILE_STEM}_GML.zip not found in the download list")


def _extract(zip_path: Path, tmp_dir: Path) -> Path:
    """zip から全国版の GeoJSON を取り出す。"""
    with zipfile.ZipFile(zip_path) as zf:
        member = next(
            (
                i
                for i in zf.infolist()
                # zip 内のパス区切りが円記号のことがあるので末尾で照合する
                if i.orig_filename.replace("\\", "/").endswith(GEOJSON_NAME)
            ),
            None,
        )
        if member is None:
            raise SystemExit(f"{GEOJSON_NAME} not found in {zip_path.name}")
        path = tmp_dir / GEOJSON_NAME
        with zf.open(member) as src, open(path, "wb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
    return path


def _convert(geojson: Path, parquet_path: Path) -> None:
    """GeoJSON を Parquet に変換する。

    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    con = duckdb.connect()
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
        con.execute(
            f"""
            COPY (
                SELECT * EXCLUDE (OGC_FID, geom), ST_AsWKB(geom) AS geom
                FROM ST_Read('{geojson.as_posix()}')
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        con.close()
    tmp_path.rename(parquet_path)


def download_did(dest_dir: str) -> None:
    """人口集中地区データを Parquet 化する。

    変換済みのファイルがあればスキップするため、途中で中断しても再実行で
    続きから処理できる（冪等）。
    """
    dest = Path(dest_dir)
    tmp_dir = dest / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = dest / f"{FILE_STEM}.parquet"

    if parquet_path.exists():
        logger.info(f"  skip {FILE_STEM} (already converted)")
        return

    html = _fetch_page()
    _check_license(html)
    url = _find_url(html)

    zip_path = tmp_dir / f"{FILE_STEM}_GML.zip"
    logger.info(f"  downloading {FILE_STEM}...")
    _download(url, zip_path)

    try:
        geojson_path = _extract(zip_path, tmp_dir)
        try:
            _convert(geojson_path, parquet_path)
        finally:
            geojson_path.unlink(missing_ok=True)
    finally:
        zip_path.unlink(missing_ok=True)

    logger.info(f"  did data ready in {dest}")
