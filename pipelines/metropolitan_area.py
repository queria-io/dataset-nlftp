"""国土数値情報 A03 三大都市圏計画区域データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から、首都圏整備法・中部圏開発整備法・
近畿圏整備法に基づく政策区域（既成市街地・近郊整備地帯・都市開発区域・保全区域・
近郊緑地保全区域など）のポリゴンを圏域単位でダウンロードし、Parquet に変換して
配置する。

配布ファイルの形式
------------------
首都圏（SYUTO）・中部圏（CHUBU）・近畿圏（KINKI）の 3 つの zip があり、それぞれに
圏域 1 ファイルの GeoJSON が入る。シェープファイルも同梱されるが、.dbf が CP932 で
DuckDB の ST_Read が読めないため GeoJSON を使う。

1 行 = 市区町村と区域の組み合わせを島や飛び地ごとに分けたポリゴン。区域の指定が
無い市区町村の部分も「無指定」の区分で入るので、圏域の全体を覆う。区域区分と
区域コードのコード値は圏域ごとに別のコードリストを持つため、圏域の識別子を
列に足して残す。

データソース: 三大都市圏計画区域（A03、2025年度版）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A03-2025.html
同じページに 2003年度版（日本測地系）も並ぶが、最新年度だけを取る。
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

PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A03-2025.html"

# 取り込む整備年度（ファイル名の A03-<yy>）
FILE_PREFIX = "A03-25"

# 圏域の識別子（ファイル名の接尾辞）
AREAS = ("SYUTO", "CHUBU", "KINKI")

# データ項目全体に付く使用許諾条件。記載が一字でも変わったら取り込みを続けない
LICENSE_TEXT = "オープンデータ（CC_BY_4.0）"

# 属性（A03_001 から）の出力列名。順番が属性番号に対応する
COLUMNS = (
    "lg_code",
    "prefecture_name",
    "district_name",
    "municipality_name",
    "surface_type_code",
    "section_type_code",
    "section_code",
    "note",
)


def _fetch_page() -> str:
    """配布ページの HTML を取得する（HTML コメントは落とす）。"""
    html = fetch_text(PAGE_URL)
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def _check_license(html: str) -> None:
    """使用許諾条件がオープンデータのままであることを確かめる。"""
    match = re.search(r"このデータの使用許諾条件(.{0,200})", html, flags=re.DOTALL)
    if match is None:
        raise SystemExit("license section not found on the distribution page")
    if LICENSE_TEXT not in re.sub(r"<[^>]+>", "", match.group(1)):
        raise SystemExit("license terms changed: open data statement not found")


def _parse_files(html: str) -> list[tuple[str, str, str]]:
    """ダウンロード一覧から (ファイル名, 圏域, URL) を取り出す。"""
    files = []
    seen = set()
    for path in re.findall(r"DownLd\([^)]*'((?:\.\./)?data/A03/[^']+\.zip)'", html):
        url = urljoin(PAGE_URL, path)
        stem = url.rsplit("/", 1)[-1].removesuffix("_GML.zip")
        match = re.fullmatch(rf"{FILE_PREFIX}_([A-Z]+)", stem)
        if not match or match.group(1) not in AREAS or stem in seen:
            continue
        seen.add(stem)
        files.append((stem, match.group(1), url))
    if len(files) != len(AREAS):
        raise SystemExit(f"A03 download list parse looks broken: {len(files)} files")
    return sorted(files)


def _extract(zip_path: Path, stem: str, tmp_dir: Path) -> Path:
    """zip から GeoJSON を取り出す。"""
    name = f"{stem}.geojson"
    with zipfile.ZipFile(zip_path) as zf:
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
        path = tmp_dir / name
        with zf.open(member) as src, open(path, "wb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
    return path


def _convert(geojson: Path, parquet_path: Path, area: str) -> None:
    """GeoJSON を Parquet に変換する。

    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    """
    columns = ",\n".join(
        f"A03_{i:03d} AS {name}" for i, name in enumerate(COLUMNS, start=1)
    )
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    con = duckdb.connect()
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
        con.execute(
            f"""
            COPY (
                SELECT
                    '{area}' AS metropolitan_area_code,
                    {columns},
                    ST_AsWKB(geom) AS geom
                FROM ST_Read('{geojson.as_posix()}')
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        con.close()
    tmp_path.rename(parquet_path)


def download_metropolitan_area(dest_dir: str) -> None:
    """三大都市圏計画区域データを圏域ごとに Parquet 化する。

    圏域ごとに zip をダウンロードして Parquet に変換し、zip は変換後すぐ
    削除する。変換済みのファイルはスキップするため、途中で中断しても再実行で
    続きから処理できる（冪等）。
    """
    dest = Path(dest_dir)
    tmp_dir = dest / "tmp"
    parquet_dir = dest / "parquet"
    for p in (tmp_dir, parquet_dir):
        p.mkdir(parents=True, exist_ok=True)

    html = _fetch_page()
    _check_license(html)
    files = _parse_files(html)
    logger.info(f"  {len(files)} area files listed")

    for stem, area, url in files:
        parquet_path = parquet_dir / f"{stem}.parquet"
        if parquet_path.exists():
            logger.info(f"  skip {stem} (already converted)")
            continue

        zip_path = tmp_dir / f"{stem}_GML.zip"
        logger.info(f"  downloading {stem}...")
        download(url, zip_path)

        try:
            geojson_path = _extract(zip_path, stem, tmp_dir)
            try:
                _convert(geojson_path, parquet_path, area)
            finally:
                geojson_path.unlink(missing_ok=True)
        finally:
            zip_path.unlink(missing_ok=True)

    logger.info(f"  A03 data ready in {dest}")
