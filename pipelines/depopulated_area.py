"""国土数値情報 A17 過疎地域データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から過疎地域データを都道府県単位で
ダウンロードし、Parquet に変換して配置する。総務省自治行政局の過疎指定地域一覧に
載る市町村・旧市町村を、行政区域データの中から抽出したポリゴンが原典。

配布ファイルの形式
------------------
zip には都道府県 1 ファイルの GeoJSON が入る。シェープファイルも同梱されるが、
.dbf が CP932 で DuckDB の ST_Read が読めないため GeoJSON を使う。

1 行 = 1 ポリゴンで、1 つの指定区域が島や飛び地の数だけ行に分かれる。区域単位の
属性（過疎ID・行政区域コード・過疎区分）は各行に繰り返し入る。

神奈川県には過疎地域の指定が無く、配布ファイル自体が存在しない（46 都道府県）。

データソース: 過疎地域（A17、2017年（平成29年）版）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A17-2017.html
"""

import logging
import os
import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import duckdb

from pipelines.download import download

logger = logging.getLogger("pipelines")

PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A17-2017.html"

# 取り込む整備年度（ファイル名の A17-<yy>）。1970年から 2016年までの過年度整備分も
# 同じページに並ぶので、最新年度だけを取る
FILE_PREFIX = "A17-17"

# データ項目全体に付く使用許諾条件。都道府県ごとの区分は無い。他の都道府県が
# 原典を作るデータ（A29 用途地域・A33 土砂災害警戒区域など）は条件付き公開の
# 区分が後から足されることがあるので、記載が一字でも変わったら取り込みを続けない
LICENSE_TEXT = "商用可"

# 神奈川県（14）には過疎地域の指定が無く、配布ファイルも無い
PREFECTURE_CODES = {f"{i:02d}" for i in range(1, 48)} - {"14"}


def _prefectures() -> set[str] | None:
    """処理対象を絞る都道府県コード。

    NLFTP_DEPOPULATED_AREA_PREFECTURES（カンマ区切り、例: "13,47"）で絞り込める。
    未指定なら全都道府県。
    """
    env = os.environ.get("NLFTP_DEPOPULATED_AREA_PREFECTURES")
    if not env:
        return None
    return {p.strip() for p in env.split(",") if p.strip()}


def _fetch_page() -> str:
    """配布ページの HTML を取得する（HTML コメントは落とす）。"""
    req = Request(PAGE_URL, headers={"User-Agent": "dataset-nlftp"})
    with urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def _check_license(html: str) -> None:
    """使用許諾条件が商用可のままであることを確かめる。"""
    match = re.search(r"このデータの使用許諾条件(.{0,200})", html, flags=re.DOTALL)
    if match is None:
        raise SystemExit("license section not found on the distribution page")
    if LICENSE_TEXT not in re.sub(r"<[^>]+>", "", match.group(1)):
        raise SystemExit("license terms changed: commercial use statement not found")


def _parse_files(html: str) -> list[tuple[str, str, str]]:
    """ダウンロード一覧から (ファイル名, 都道府県コード, URL) を取り出す。"""
    files = []
    seen = set()
    for path in re.findall(r"DownLd\([^)]*'((?:\.\./)?data/A17/[^']+\.zip)'", html):
        url = urljoin(PAGE_URL, path)
        stem = url.rsplit("/", 1)[-1].removesuffix("_GML.zip")
        match = re.fullmatch(rf"{FILE_PREFIX}_(\d{{2}})", stem)
        if not match or match.group(1) not in PREFECTURE_CODES or stem in seen:
            continue
        seen.add(stem)
        files.append((stem, match.group(1), url))
    if len(files) != len(PREFECTURE_CODES):
        raise SystemExit(f"download list parse looks broken: {len(files)} files")
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


def _convert(geojson: Path, parquet_path: Path, pref: str) -> None:
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
                SELECT
                    '{pref}' AS prefecture_code,
                    A17_001 AS area_code,
                    A17_002 AS lg_code,
                    A17_004 AS subprefecture_name,
                    A17_005 AS district_name,
                    A17_006 AS municipality_name,
                    A17_007 AS source_municipality_name,
                    A17_008 AS former_municipality_name,
                    A17_009 AS category_code,
                    ST_AsWKB(geom) AS geom
                FROM ST_Read('{geojson.as_posix()}')
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        con.close()
    tmp_path.rename(parquet_path)


def download_depopulated_area(dest_dir: str) -> None:
    """過疎地域データを都道府県ごとに Parquet 化する。

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
    _check_license(html)
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
            geojson_path = _extract(zip_path, stem, tmp_dir)
            try:
                _convert(geojson_path, parquet_path, pref)
            finally:
                geojson_path.unlink(missing_ok=True)
        finally:
            zip_path.unlink(missing_ok=True)

    logger.info(f"  depopulated area data ready in {dest}")
