"""国土数値情報 A29 用途地域データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から用途地域データ
（令和元年度・第2.1版）を都道府県単位でダウンロードし、市区町村ごとの
GeoJSON を都道府県ごとの Parquet に変換して配置する。

利用条件による絞り込み
----------------------
用途地域データは原典資料を作成した市区町村ごとに公開条件が異なる。
提供元が配布する「公開に関する利用条件」（市区町村別の一覧）では

  1. オープンデータ公開可
  2. 条件を付して公開可（有償利用不可 / 再配信不可）
  3. 公開不可
  4. 回答なし

の 4 区分が示されており、配布 zip には 1 と 2 が含まれる。ここでは 1 の
市区町村のみを取り込む（2 は有償利用不可・再配信不可が付くため）。
判定は利用条件一覧（PDF）を毎回取得して行い、zip に含まれる市区町村が
一覧に載っていない場合は判定できないためエラーで停止する。

GeoJSON の属性 A29_008（備考）にも公開条件らしき文字列が入ることがあるが、
都道府県ごとに表記が揺れる自由記述のため判定には使わない。

データソース: 用途地域データ（A29、第2.1版・令和元年度）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A29-v2_1.html
"""

import logging
import os
import re
import shutil
import zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import duckdb
from pypdf import PdfReader

logger = logging.getLogger("pipelines")

URL_TEMPLATE = "https://nlftp.mlit.go.jp/ksj/gml/data/A29/A29-19/A29-19_{pref}_GML.zip"

# 市区町村別の公開に関する利用条件（提供元が配布する PDF）
TERMS_URL = (
    "https://nlftp.mlit.go.jp/ksj/gml/datalist/"
    "Situation_of_the_data_collection_RestrictedZoneData.pdf"
)

# 利用条件一覧の公開可否区分。取り込むのは OPEN_CATEGORY のみ
DISCLOSURE_LABELS = {
    1: "オープンデータ公開可",
    2: "条件を付して公開可",
    3: "公開不可",
    4: "回答なし",
}
OPEN_CATEGORY = 1

# 利用条件一覧のパース結果が壊れていないことを確かめる下限
# （令和元年度版は 1,213 市区町村・うちオープンデータ公開可 960）
MIN_TERMS_ROWS = 1000
MIN_OPEN_ROWS = 800

PREFECTURES = [f"{i:02d}" for i in range(1, 48)]

# zip 内の UTF-8 GeoJSON（シェープファイルの .dbf は Shift-JIS で文字化けする）
GEOJSON_DIR = "01-03_GeoJSON形式"

CREATE_TABLE_SQL = """
CREATE OR REPLACE TEMP TABLE zoning (
    admin_code VARCHAR,
    prefecture_name VARCHAR,
    municipality_name VARCHAR,
    zoning_code INTEGER,
    source_zoning_name VARCHAR,
    building_coverage_ratio INTEGER,
    floor_area_ratio INTEGER,
    geom BLOB
)
"""


def _prefectures() -> list[str]:
    """処理対象の都道府県コード一覧。

    NLFTP_ZONING_PREFECTURES（カンマ区切り、例: "06,13"）で絞り込める。
    未指定なら全国（01〜47）。
    """
    env = os.environ.get("NLFTP_ZONING_PREFECTURES")
    if env:
        return [p.strip() for p in env.split(",") if p.strip()]
    return PREFECTURES


def _decode_member_name(name: str) -> str:
    """zip 内のファイル名を CP932 として復元する。

    A29 の zip はファイル名が CP932 でエンコードされているため、
    Python zipfile が CP437 として解釈した文字列を元に戻す。
    復元できない場合はそのまま返す。
    """
    try:
        return name.encode("cp437").decode("cp932")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def _admin_codes_in_zip(zip_path: Path) -> list[str]:
    """zip に含まれる市区町村コードの一覧（GeoJSON のファイル名から取る）。"""
    codes = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            decoded = _decode_member_name(info.filename).replace("\\", "/")
            if GEOJSON_DIR not in decoded or not decoded.endswith(".geojson"):
                continue
            basename = decoded.rsplit("/", 1)[-1]
            codes.append(basename.removesuffix(".geojson").split("_")[-1])
    return codes


def _download(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "dataset-nlftp"})
    with urlopen(req) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f, 1024 * 1024)


def _zenkaku(value: int) -> str:
    """半角数字を全角数字に変換する（PDF の区分番号が全角のため）。"""
    return str(value).translate(str.maketrans("0123456789", "０１２３４５６７８９"))


def _parse_terms(pdf_path: Path) -> dict[str, int]:
    """利用条件一覧 PDF を市区町村コード → 公開可否区分の辞書にする。

    行頭が 5 桁の行政コードの行を 1 市区町村として読み、区分名の有無で
    分類する。区分名が読み取れない行は 0（判定不能）とし、取り込み対象から
    外す（判定できないものは公開しない）。
    """
    reader = PdfReader(str(pdf_path))
    lines: list[str] = []
    for page in reader.pages:
        lines += page.extract_text().split("\n")

    categories: dict[str, int] = {}
    for line in lines:
        if not re.match(r"^\d{5}\s", line):
            continue
        category = 0
        for value, label in DISCLOSURE_LABELS.items():
            if f"{_zenkaku(value)}．{label}" in line:
                category = value
                break
        categories[line[:5]] = category
    return categories


def _load_disclosure_terms(dest: Path) -> dict[str, int]:
    """利用条件一覧を取得してパースする。"""
    pdf_path = dest / "disclosure_terms.pdf"
    logger.info("  downloading disclosure terms...")
    _download(TERMS_URL, pdf_path)
    try:
        categories = _parse_terms(pdf_path)
    finally:
        pdf_path.unlink(missing_ok=True)

    open_codes = [c for c, v in categories.items() if v == OPEN_CATEGORY]
    if len(categories) < MIN_TERMS_ROWS or len(open_codes) < MIN_OPEN_ROWS:
        raise SystemExit(
            "disclosure terms parse looks broken: "
            f"{len(categories)} municipalities / {len(open_codes)} open"
        )

    logger.info(
        f"  disclosure terms: {len(categories)} municipalities, "
        f"{len(open_codes)} open data"
    )
    return categories


def _write_license(dest: Path, categories: dict[str, int]) -> None:
    """市区町村別の公開可否区分を Parquet に書き出す。"""
    con = duckdb.connect()
    try:
        con.execute(
            "CREATE TEMP TABLE license (admin_code VARCHAR, "
            "disclosure_category INTEGER, disclosure_label VARCHAR)"
        )
        con.executemany(
            "INSERT INTO license VALUES (?, ?, ?)",
            [
                (code, value, DISCLOSURE_LABELS.get(value))
                for code, value in sorted(categories.items())
            ],
        )
        con.execute(
            f"COPY license TO '{(dest / 'license.parquet').as_posix()}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        con.close()


def _convert_prefecture(
    con: duckdb.DuckDBPyConnection,
    zip_path: Path,
    tmp_dir: Path,
    parquet_path: Path,
    open_codes: set[str],
) -> tuple[int, int]:
    """zip 内のオープンデータ公開可の市区町村を 1 つの Parquet にまとめる。

    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    戻り値は (取り込んだ市区町村数, 利用条件により除外した市区町村数)。
    """
    con.execute(CREATE_TABLE_SQL)

    included = 0
    excluded = 0
    geojson_path = tmp_dir / "current.geojson"
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            decoded = _decode_member_name(info.filename).replace("\\", "/")
            if GEOJSON_DIR not in decoded or not decoded.endswith(".geojson"):
                continue

            basename = decoded.rsplit("/", 1)[-1]
            admin_code = basename.removesuffix(".geojson").split("_")[-1]
            if admin_code not in open_codes:
                excluded += 1
                continue

            with zf.open(info) as src, open(geojson_path, "wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            try:
                con.execute(
                    f"""
                    INSERT INTO zoning
                    SELECT
                        CAST(A29_001 AS VARCHAR),
                        CAST(A29_002 AS VARCHAR),
                        CAST(A29_003 AS VARCHAR),
                        TRY_CAST(A29_004 AS INTEGER),
                        CAST(A29_005 AS VARCHAR),
                        TRY_CAST(A29_006 AS INTEGER),
                        TRY_CAST(A29_007 AS INTEGER),
                        ST_AsWKB(geom)
                    FROM ST_Read('{geojson_path.as_posix()}')
                    """
                )
            finally:
                geojson_path.unlink(missing_ok=True)
            included += 1

    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    con.execute(
        f"COPY zoning TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    tmp_path.rename(parquet_path)
    return included, excluded


def download_zoning(dest_dir: str) -> None:
    """用途地域データ（オープンデータ公開可の市区町村のみ）を Parquet 化する。

    都道府県ごとに zip をダウンロードし、オープンデータ公開可の市区町村の
    GeoJSON だけを 1 つの Parquet にまとめる。zip・GeoJSON は変換後すぐ
    削除する。変換済みの都道府県はスキップするため、途中で中断しても
    再実行で続きから処理できる（冪等）。
    """
    dest = Path(dest_dir)
    parquet_dir = dest / "parquet"
    tmp_dir = dest / "tmp"
    for d in (parquet_dir, tmp_dir):
        d.mkdir(parents=True, exist_ok=True)

    categories = _load_disclosure_terms(dest)
    open_codes = {c for c, v in categories.items() if v == OPEN_CATEGORY}
    _write_license(dest, categories)

    for pref in _prefectures():
        parquet_path = parquet_dir / f"{pref}.parquet"
        if parquet_path.exists():
            logger.info(f"  skip A29-19_{pref} (already converted)")
            continue

        url = URL_TEMPLATE.format(pref=pref)
        zip_path = tmp_dir / f"A29-19_{pref}_GML.zip"
        logger.info(f"  downloading A29-19_{pref}...")
        try:
            _download(url, zip_path)
        except HTTPError as e:
            if e.code == 404:
                logger.info(f"  skip A29-19_{pref} (not found)")
                continue
            raise

        unknown = sorted(set(_admin_codes_in_zip(zip_path)) - set(categories))
        if unknown:
            raise SystemExit(
                f"municipalities missing from disclosure terms: {unknown}"
            )

        con = duckdb.connect()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            included, excluded = _convert_prefecture(
                con, zip_path, tmp_dir, parquet_path, open_codes
            )
        finally:
            con.close()
            zip_path.unlink(missing_ok=True)

        logger.info(
            f"  A29-19_{pref}: {included} municipalities converted, "
            f"{excluded} excluded by disclosure terms"
        )

    logger.info(f"  zoning data ready in {parquet_dir}")
