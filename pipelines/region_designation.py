"""国土数値情報の地域指定データ（A23 特殊土壌地帯 / A25 特定農山村地域）のダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から、法律に基づいて指定された
市町村・旧市町村の区域のポリゴンを都道府県単位でダウンロードし、Parquet に
変換して配置する。どちらも行政区域データの中から指定区域を抽出したもので、
配布の形も属性の並びも同じなので、1 つの取得処理を 2 つの設定で使う。

配布ファイルの形式
------------------
zip には都道府県 1 ファイルの GeoJSON が入る。シェープファイルも同梱されるが、
.dbf が CP932 で DuckDB の ST_Read が読めないため GeoJSON を使う。

1 行 = 1 ポリゴンで、1 つの指定区域が島や飛び地の数だけ行に分かれる。区域単位の
属性（ID・行政区域コード・名称など）は各行に繰り返し入る。

データソース:
- 特殊土壌地帯（A23、2016年（平成28年）版）
  https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A23-2016.html
  指定のある 14 県だけが配布される。
- 特定農山村地域（A25、2016年（平成28年）版）
  https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A25-2016.html
  47 都道府県すべてが配布される。
"""

import logging
import os
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import duckdb

from pipelines.download import download, fetch_text

logger = logging.getLogger("pipelines")

# データ項目全体に付く使用許諾条件。都道府県ごとの区分は無い。他の都道府県が
# 原典を作るデータ（A29 用途地域・A33 土砂災害警戒区域など）は条件付き公開の
# 区分が後から足されることがあるので、記載が一字でも変わったら取り込みを続けない
LICENSE_TEXT = "商用可"


@dataclass(frozen=True)
class Designation:
    # 国土数値情報の識別子（A23 など）。属性名の接頭辞にもなる
    code: str
    page_url: str
    # 取り込む整備年度（ファイル名の A23-<yy>）。過年度整備分も同じページに
    # 並ぶので、最新年度だけを取る
    file_prefix: str
    prefecture_codes: frozenset[str]
    # 属性（<code>_001 から）の出力列名。順番が属性番号に対応する
    columns: tuple[str, ...]
    # 処理対象の都道府県を絞る環境変数
    env: str


SPECIAL_SOIL_AREA = Designation(
    code="A23",
    page_url="https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A23-2016.html",
    file_prefix="A23-16",
    # 特殊土壌地帯の指定がある 14 県
    prefecture_codes=frozenset("22 28 31 32 33 34 35 38 39 40 43 44 45 46".split()),
    columns=(
        "area_code",
        "lg_code",
        "prefecture_name",
        "subprefecture_name",
        "district_name",
        "municipality_name",
        "source_municipality_name",
        "former_municipality_name",
        "category_code",
    ),
    env="NLFTP_SPECIAL_SOIL_AREA_PREFECTURES",
)

SPECIFIED_RURAL_AREA = Designation(
    code="A25",
    page_url="https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A25-2016.html",
    file_prefix="A25-16",
    prefecture_codes=frozenset(f"{i:02d}" for i in range(1, 48)),
    columns=(
        "area_code",
        "lg_code",
        "prefecture_name",
        "subprefecture_name",
        "district_name",
        "municipality_name",
        "source_municipality_name",
        "former_municipality_name",
    ),
    env="NLFTP_SPECIFIED_RURAL_AREA_PREFECTURES",
)


def _prefectures(d: Designation) -> set[str] | None:
    """処理対象を絞る都道府県コード。

    d.env（カンマ区切り、例: "13,47"）で絞り込める。未指定なら全都道府県。
    """
    env = os.environ.get(d.env)
    if not env:
        return None
    return {p.strip() for p in env.split(",") if p.strip()}


def _fetch_page(d: Designation) -> str:
    """配布ページの HTML を取得する（HTML コメントは落とす）。"""
    html = fetch_text(d.page_url)
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def _check_license(html: str) -> None:
    """使用許諾条件が商用可のままであることを確かめる。"""
    match = re.search(r"このデータの使用許諾条件(.{0,200})", html, flags=re.DOTALL)
    if match is None:
        raise SystemExit("license section not found on the distribution page")
    if LICENSE_TEXT not in re.sub(r"<[^>]+>", "", match.group(1)):
        raise SystemExit("license terms changed: commercial use statement not found")


def _parse_files(d: Designation, html: str) -> list[tuple[str, str, str]]:
    """ダウンロード一覧から (ファイル名, 都道府県コード, URL) を取り出す。"""
    files = []
    seen = set()
    pattern = rf"DownLd\([^)]*'((?:\.\./)?data/{d.code}/[^']+\.zip)'"
    for path in re.findall(pattern, html):
        url = urljoin(d.page_url, path)
        stem = url.rsplit("/", 1)[-1].removesuffix("_GML.zip")
        match = re.fullmatch(rf"{d.file_prefix}_(\d{{2}})", stem)
        if not match or match.group(1) not in d.prefecture_codes or stem in seen:
            continue
        seen.add(stem)
        files.append((stem, match.group(1), url))
    if len(files) != len(d.prefecture_codes):
        raise SystemExit(
            f"{d.code} download list parse looks broken: {len(files)} files"
        )
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


def _convert(d: Designation, geojson: Path, parquet_path: Path, pref: str) -> None:
    """GeoJSON を Parquet に変換する。

    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    """
    columns = ",\n".join(
        f"{d.code}_{i:03d} AS {name}" for i, name in enumerate(d.columns, start=1)
    )
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    con = duckdb.connect()
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
        con.execute(
            f"""
            COPY (
                SELECT
                    '{pref}' AS prefecture_code,
                    {columns},
                    ST_AsWKB(geom) AS geom
                FROM ST_Read('{geojson.as_posix()}')
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        con.close()
    tmp_path.rename(parquet_path)


def _download(d: Designation, dest_dir: str) -> None:
    """地域指定データを都道府県ごとに Parquet 化する。

    都道府県ごとに zip をダウンロードして Parquet に変換し、zip は変換後すぐ
    削除する。変換済みのファイルはスキップするため、途中で中断しても再実行で
    続きから処理できる（冪等）。
    """
    dest = Path(dest_dir)
    tmp_dir = dest / "tmp"
    parquet_dir = dest / "parquet"
    for p in (tmp_dir, parquet_dir):
        p.mkdir(parents=True, exist_ok=True)

    html = _fetch_page(d)
    _check_license(html)
    files = _parse_files(d, html)
    logger.info(f"  {len(files)} prefecture files listed")

    only = _prefectures(d)
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
            geojson_path = _extract(zip_path, stem, tmp_dir)
            try:
                _convert(d, geojson_path, parquet_path, pref)
            finally:
                geojson_path.unlink(missing_ok=True)
        finally:
            zip_path.unlink(missing_ok=True)

    logger.info(f"  {d.code} data ready in {dest}")


def download_special_soil_area(dest_dir: str) -> None:
    """特殊土壌地帯データ（A23）を都道府県ごとに Parquet 化する。"""
    _download(SPECIAL_SOIL_AREA, dest_dir)


def download_specified_rural_area(dest_dir: str) -> None:
    """特定農山村地域データ（A25）を都道府県ごとに Parquet 化する。"""
    _download(SPECIFIED_RURAL_AREA, dest_dir)
