"""国土数値情報 W09 湖沼データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から湖沼データ（全国 1 ファイル）を
ダウンロードし、Parquet に変換して配置する。全国の湖沼と貯水池の範囲を面で持ち、
湖沼名・行政区域コード・最大水深・水面標高を属性に持つ。

配布の範囲
----------
使用許諾は「商用可」。整備年度は 2005 年版だけで、全国版の zip が 1 つある。

配布ファイルの形式
------------------
2005 年版の zip には GeoJSON が無く、シェープファイルと GML だけが入る。
シェープファイルには .prj が無い（座標系は JGD2000 の緯度経度）。
.dbf は CP932 で湖沼名に日本語が入り、DuckDB の ST_Read では読み込みごと
失敗するので、.dbf は ST_Read に渡さず属性だけ自前でデコードし、
レコード順で幾何と突き合わせる。

データソース: 湖沼（W09、2005年）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-W09-2005.html
"""

import logging
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import duckdb

from pipelines.download import download, fetch_text
from pipelines.tsunami import _read_dbf_column

logger = logging.getLogger("pipelines")

PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-W09-2005.html"

# 取り込む版（ファイル名の W09-<yy>）
FILE_STEM = "W09-05"

# zip 内のシェープファイルの名前（拡張子を除く）
SHAPEFILE_STEM = "W09-05-g_Lake"

ATTRIBUTE_COLUMNS = ("W09_001", "W09_002", "W09_003", "W09_004")


def _zip_url() -> str:
    """配布ページから全国版の zip の URL を取り出す。"""
    html = fetch_text(PAGE_URL)
    name = f"{FILE_STEM}_GML.zip"
    if f"'{name}'" not in html:
        raise SystemExit(f"download list changed: {name} not found on {PAGE_URL}")
    return urljoin(PAGE_URL, f"../data/W09/{FILE_STEM}/{name}")


def _convert(zip_path: Path, tmp_dir: Path, parquet_path: Path) -> None:
    """シェープファイルの幾何と .dbf の属性をレコード順で突き合わせて Parquet にする。

    ST_Read が返す OGC_FID はシェープファイルのレコード番号（0 始まり）で、
    .dbf のレコード順と一致する。件数が食い違うときは対応が取れないので止める。
    """
    extracted = []
    with zipfile.ZipFile(zip_path) as zf:
        members = {
            i.filename.replace("\\", "/").rsplit("/", 1)[-1]: i for i in zf.infolist()
        }
        for suffix in (".shp", ".shx"):
            name = SHAPEFILE_STEM + suffix
            if name not in members:
                raise SystemExit(f"{name} not found in {zip_path.name}")
            path = tmp_dir / name
            with zf.open(members[name]) as src, open(path, "wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            extracted.append(path)
        dbf_name = SHAPEFILE_STEM + ".dbf"
        if dbf_name not in members:
            raise SystemExit(f"{dbf_name} not found in {zip_path.name}")
        dbf = zf.read(members[dbf_name])

    columns = [_read_dbf_column(dbf, c) for c in ATTRIBUTE_COLUMNS]
    shp_path = tmp_dir / f"{SHAPEFILE_STEM}.shp"
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    con = duckdb.connect()
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
        (count,) = con.execute(
            f"SELECT count(*) FROM ST_Read('{shp_path.as_posix()}')"
        ).fetchone()
        if count != len(columns[0]):
            raise SystemExit(
                f"shapefile/dbf record mismatch: {count} shapes / {len(columns[0])} attributes"
            )

        con.execute(
            "CREATE TEMP TABLE attributes "
            "(fid BIGINT, W09_001 VARCHAR, W09_002 VARCHAR, W09_003 VARCHAR, W09_004 VARCHAR)"
        )
        con.executemany(
            "INSERT INTO attributes VALUES (?, ?, ?, ?, ?)",
            [(i, *values) for i, values in enumerate(zip(*columns))],
        )
        con.execute(
            f"""
            COPY (
                SELECT
                    s.OGC_FID AS record_number,
                    a.W09_001 AS lake_name,
                    a.W09_002 AS lg_codes,
                    a.W09_003 AS max_depth_m,
                    a.W09_004 AS water_surface_elevation_m,
                    ST_AsWKB(s.geom) AS geom
                FROM ST_Read('{shp_path.as_posix()}') AS s
                JOIN attributes AS a ON a.fid = s.OGC_FID
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        con.close()
        for path in extracted:
            path.unlink(missing_ok=True)
    tmp_path.rename(parquet_path)


def download_lake(dest_dir: str) -> None:
    """湖沼データを Parquet 化する。

    全国版の zip をダウンロードして Parquet に変換し、zip は変換後すぐ削除する。
    変換済みならスキップする（冪等）。
    """
    dest = Path(dest_dir)
    tmp_dir = dest / "tmp"
    parquet_dir = dest / "parquet"
    for d in (tmp_dir, parquet_dir):
        d.mkdir(parents=True, exist_ok=True)

    parquet_path = parquet_dir / f"{FILE_STEM}.parquet"
    if parquet_path.exists():
        logger.info(f"  skip {FILE_STEM} (already converted)")
        return

    url = _zip_url()
    zip_path = tmp_dir / f"{FILE_STEM}_GML.zip"
    logger.info(f"  downloading {FILE_STEM}...")
    download(url, zip_path)
    try:
        _convert(zip_path, tmp_dir, parquet_path)
    finally:
        zip_path.unlink(missing_ok=True)

    logger.info(f"  lake data ready in {parquet_dir}")
