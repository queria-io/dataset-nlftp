"""国土数値情報 G08 低位地帯データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から低位地帯データを都道府県
単位でダウンロードし、Parquet に変換して配置する。低位地帯は周辺よりも
標高が低く凹んでいる土地で、標高メッシュから抽出した 1ha 以上の凹地を
収録する。

配布の範囲
----------
使用許諾は「商用可」。整備年度は 2015 年度だけで、47 都道府県すべてに
配布がある。

配布ファイルの形式
------------------
2015 年度版の zip には GeoJSON が無く、シェープファイルと GML だけが入る。
属性は数値 2 つと 1 桁のコードだけで日本語の文字列を持たないので、
.dbf の文字コードに関係なく DuckDB の ST_Read でシェープファイルを読める。

データソース: 低位地帯（G08、2015年度）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-G08-2015.html
"""

import logging
import os
import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import duckdb

from pipelines.download import download, fetch_text

logger = logging.getLogger("pipelines")

PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-G08-2015.html"

# 取り込む整備年度（ファイル名の G08-<yy>）
FILE_PREFIX = "G08-15"

PREFECTURE_CODES = {f"{i:02d}" for i in range(1, 48)}

# シェープファイルとして読むのに要る構成ファイル
SHAPEFILE_SUFFIXES = (".shp", ".shx", ".dbf", ".prj")


def _prefectures() -> set[str] | None:
    """処理対象を絞る都道府県コード。

    NLFTP_LOWLAND_PREFECTURES（カンマ区切り、例: "13,47"）で絞り込める。
    未指定なら 47 都道府県すべて。
    """
    env = os.environ.get("NLFTP_LOWLAND_PREFECTURES")
    if not env:
        return None
    return {p.strip() for p in env.split(",") if p.strip()}


def _fetch_page() -> str:
    """配布ページの HTML を取得する（HTML コメントは落とす）。"""
    html = fetch_text(PAGE_URL)
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def _parse_files(html: str) -> list[tuple[str, str, str]]:
    """ダウンロード一覧から (ファイル名, 都道府県コード, URL) を取り出す。"""
    files = []
    seen = set()
    for path in re.findall(r"DownLd\([^)]*'([^']+\.zip)'", html):
        url = urljoin(PAGE_URL, path)
        stem = url.rsplit("/", 1)[-1].removesuffix("_GML.zip")
        match = re.fullmatch(rf"{FILE_PREFIX}_(\d{{2}})", stem)
        if not match or match.group(1) not in PREFECTURE_CODES or stem in seen:
            continue
        seen.add(stem)
        files.append((stem, match.group(1), url))
    missing = sorted(PREFECTURE_CODES - {pref for _, pref, _ in files})
    if missing:
        raise SystemExit(f"download list changed: prefectures missing {missing}")
    return sorted(files)


def _extract(zip_path: Path, stem: str, tmp_dir: Path) -> Path:
    """zip からシェープファイルの構成ファイルを取り出し、.shp のパスを返す。"""
    with zipfile.ZipFile(zip_path) as zf:
        for suffix in SHAPEFILE_SUFFIXES:
            name = f"{stem}{suffix}"
            member = next(
                (
                    i
                    for i in zf.infolist()
                    # zip 内のパス区切りが円記号のことがあるので末尾で照合する
                    if i.orig_filename.replace("\\", "/").endswith(name)
                ),
                None,
            )
            if member is None:
                raise SystemExit(f"{name} not found in {zip_path.name}")
            with zf.open(member) as src, open(tmp_dir / name, "wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
    return tmp_dir / f"{stem}.shp"


def _convert(shp: Path, parquet_path: Path, pref: str) -> None:
    """シェープファイルを Parquet に変換する。

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
                SELECT
                    '{pref}' AS prefecture_code,
                    CAST(G08_001 AS DOUBLE) AS area_ha,
                    CAST(G08_002 AS DOUBLE) AS max_inundation_depth_m,
                    CAST(G08_003 AS VARCHAR) AS reference_data_code,
                    ST_AsWKB(geom) AS geom
                FROM ST_Read('{shp.as_posix()}')
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        con.close()
    tmp_path.rename(parquet_path)


def download_lowland(dest_dir: str) -> None:
    """低位地帯データを Parquet 化する。

    都道府県ごとに zip をダウンロードして Parquet に変換し、zip は変換後すぐ
    削除する。変換済みのファイルはスキップするため、途中で中断しても再実行で
    続きから処理できる（冪等）。
    """
    dest = Path(dest_dir)
    tmp_dir = dest / "tmp"
    parquet_dir = dest / "parquet"
    for d in (tmp_dir, parquet_dir):
        d.mkdir(parents=True, exist_ok=True)

    html = _fetch_page()
    files = _parse_files(html)
    logger.info(f"  {len(files)} prefecture files listed")

    only = _prefectures()
    for stem, pref, url in files:
        if only is not None and pref not in only:
            continue

        parquet_path = parquet_dir / f"{stem}.parquet"
        if parquet_path.exists():
            logger.info(f"  skip {stem} (already converted)")
            continue

        zip_path = tmp_dir / f"{stem}_GML.zip"
        logger.info(f"  downloading {stem}...")
        download(url, zip_path)

        try:
            shp_path = _extract(zip_path, stem, tmp_dir)
            try:
                _convert(shp_path, parquet_path, pref)
            finally:
                for suffix in SHAPEFILE_SUFFIXES:
                    shp_path.with_suffix(suffix).unlink(missing_ok=True)
        finally:
            zip_path.unlink(missing_ok=True)

    logger.info(f"  lowland data ready in {parquet_dir}")
