"""国土数値情報 A54 大規模盛土造成地データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から大規模盛土造成地データの
全国版をダウンロードし、Parquet に変換して配置する。谷や沢を埋めたり
傾斜地盤上に盛土したりした大規模な造成地の概ねの範囲を、市町村が
造成前後の地形図を重ねて抽出したもの。

配布の範囲
----------
使用許諾は CC BY 4.0。最新は 2023 年版で、47 都道府県すべてに配布がある。
全国版の zip に都道府県ごとの GeoJSON が 47 ファイル入っているので、
都道府県単位の zip ではなく全国版を 1 回だけ取る。

配布ファイルの形式
------------------
全国版はシェープファイル（59.6MB）・GML・GeoJSON（38.7MB）の 3 形式で
配られている。GeoJSON は 1 都道府県 1 ファイルで構成ファイルを揃える
手間が無く、zip も最も小さいので GeoJSON を使う。

データソース: 大規模盛土造成地（A54、2023年）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A54-2023.html
"""

import logging
import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import duckdb

from pipelines.download import download, fetch_text

logger = logging.getLogger("pipelines")

PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A54-2023.html"

# 取り込む版（ファイル名の A54-<yy>）
FILE_PREFIX = "A54-23"

PREFECTURE_CODES = {f"{i:02d}" for i in range(1, 48)}


def _fetch_page() -> str:
    """配布ページの HTML を取得する（HTML コメントは落とす）。"""
    html = fetch_text(PAGE_URL)
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def _national_url(html: str) -> str:
    """ダウンロード一覧から全国版 GeoJSON の zip の URL を取り出す。"""
    for path in re.findall(r"DownLd\([^)]*'([^']+\.zip)'", html):
        url = urljoin(PAGE_URL, path)
        if url.rsplit("/", 1)[-1] == f"{FILE_PREFIX}_GEOJSON.zip":
            return url
    raise SystemExit(f"download list changed: {FILE_PREFIX}_GEOJSON.zip not found")


def _extract(zip_path: Path, tmp_dir: Path) -> list[Path]:
    """zip から都道府県ごとの GeoJSON を取り出す。"""
    paths = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            # zip 内のパス区切りが円記号のことがあるので末尾で照合する
            name = info.orig_filename.replace("\\", "/").rsplit("/", 1)[-1]
            match = re.fullmatch(rf"{FILE_PREFIX}_(\d{{2}})\.geojson", name)
            if not match:
                continue
            path = tmp_dir / name
            with zf.open(info) as src, open(path, "wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            paths.append(path)
    found = {p.name[len(FILE_PREFIX) + 1 : len(FILE_PREFIX) + 3] for p in paths}
    missing = sorted(PREFECTURE_CODES - found)
    if missing:
        raise SystemExit(f"{zip_path.name} changed: prefectures missing {missing}")
    return sorted(paths)


def _convert(geojsons: list[Path], parquet_path: Path) -> None:
    """GeoJSON を 1 つの Parquet に変換する。

    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    query = " UNION ALL ".join(
        f"""
        SELECT
            CAST(A54_002 AS VARCHAR) AS prefecture_code,
            CAST(A54_004 AS VARCHAR) AS municipality_code,
            CAST(A54_005 AS VARCHAR) AS municipality_name,
            CAST(A54_001 AS VARCHAR) AS fill_type_code,
            CAST(A54_006 AS VARCHAR) AS fill_number,
            ST_AsWKB(geom) AS geom
        FROM ST_Read('{path.as_posix()}')
        """
        for path in geojsons
    )
    con = duckdb.connect()
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
        con.execute(
            f"COPY ({query}) TO '{tmp_path.as_posix()}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        con.close()
    tmp_path.rename(parquet_path)


def download_large_fill(dest_dir: str) -> None:
    """大規模盛土造成地データを Parquet 化する。

    変換済みの Parquet があればスキップする（冪等）。
    """
    dest = Path(dest_dir)
    tmp_dir = dest / "tmp"
    parquet_dir = dest / "parquet"
    for d in (tmp_dir, parquet_dir):
        d.mkdir(parents=True, exist_ok=True)

    parquet_path = parquet_dir / f"{FILE_PREFIX}.parquet"
    if parquet_path.exists():
        logger.info(f"  skip {FILE_PREFIX} (already converted)")
        return

    url = _national_url(_fetch_page())
    zip_path = tmp_dir / f"{FILE_PREFIX}_GEOJSON.zip"
    logger.info(f"  downloading {FILE_PREFIX}...")
    download(url, zip_path)

    try:
        geojsons = _extract(zip_path, tmp_dir)
        try:
            _convert(geojsons, parquet_path)
        finally:
            for path in geojsons:
                path.unlink(missing_ok=True)
    finally:
        zip_path.unlink(missing_ok=True)

    logger.info(f"  large fill data ready in {parquet_dir}")
