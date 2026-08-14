"""国土数値情報 A38 医療圏データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から医療圏データを都道府県単位で
ダウンロードし、Parquet に変換して配置する。医療法に基づいて都道府県が定める
地域保健医療計画の中で設定された一次・二次・三次医療圏の区域を、行政区域データ
から作成したものが原典。

配布ファイルの形式
------------------
zip には一次（`_1`）・二次（`_2`）・三次（`_3`）の 3 つの GeoJSON が入る。
シェープファイルも同梱されるが .dbf が CP932 で DuckDB の ST_Read が読めない
ため GeoJSON を使う。

いずれのファイルも 1 行 = 1 ポリゴンで、1 つの医療圏が複数の行に分かれる。
属性は医療圏単位の値が各行に繰り返し入る（二次医療圏の構成市区町村は 1 つの
セルにカンマ区切りで入る）。医療圏単位への集約は dbt 側で行う。

一次医療圏は市区町村と同じ区域なので、ジオメトリは取り込まない（行政区域は
boundary スキーマが持つ）。市区町村と二次医療圏の対応表として属性だけを残す。

データソース: 医療圏（A38、2020年度版）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A38-2020.html
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

logger = logging.getLogger("pipelines")

PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A38-2020.html"

# 取り込む整備年度（ファイル名の A38-<yy>）。過年度整備分（2014年度）も同じ
# ページに並ぶので、最新年度だけを取る
FILE_PREFIX = "A38-20"

# データ項目全体に付く使用許諾条件。都道府県ごとの区分は無い。他の都道府県が
# 原典を作るデータ（A29 用途地域・A33 土砂災害警戒区域など）は条件付き公開の
# 区分が後から足されることがあるので、記載が一字でも変わったら取り込みを続けない
LICENSE_TEXT = "オープンデータ（CC_BY_4.0）"

PREFECTURE_CODES = {f"{i:02d}" for i in range(1, 48)}

# 医療圏の種別ごとの GeoJSON（zip 内のファイル名の接尾辞）と出力先
LAYERS = ("primary", "secondary", "tertiary")


def _prefectures() -> set[str] | None:
    """処理対象を絞る都道府県コード。

    NLFTP_MEDICAL_AREA_PREFECTURES（カンマ区切り、例: "13,47"）で絞り込める。
    未指定なら全都道府県。
    """
    env = os.environ.get("NLFTP_MEDICAL_AREA_PREFECTURES")
    if not env:
        return None
    return {p.strip() for p in env.split(",") if p.strip()}


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
    """使用許諾条件がオープンデータのままであることを確かめる。"""
    match = re.search(r"このデータの使用許諾条件(.{0,200})", html, flags=re.DOTALL)
    if match is None:
        raise SystemExit("license section not found on the distribution page")
    if LICENSE_TEXT not in re.sub(r"<[^>]+>", "", match.group(1)):
        raise SystemExit("license terms changed: open data statement not found")


def _parse_files(html: str) -> list[tuple[str, str, str]]:
    """ダウンロード一覧から (ファイル名, 都道府県コード, URL) を取り出す。

    一覧には過年度整備分と全国のまとめも並ぶ。最新年度の都道府県単位の
    zip だけを拾う（全国のファイルは都道府県コードを持たないので落ちる）。
    """
    files = []
    seen = set()
    for path in re.findall(r"DownLd\([^)]*'((?:\.\./)?data/A38/[^']+\.zip)'", html):
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


def _extract(zip_path: Path, stem: str, tmp_dir: Path) -> dict[str, Path]:
    """zip から 3 種類の GeoJSON を取り出す。"""
    paths = {}
    with zipfile.ZipFile(zip_path) as zf:
        for index, layer in enumerate(LAYERS, start=1):
            suffix = f"{stem}_{index}.geojson"
            member = next(
                (
                    i
                    for i in zf.infolist()
                    # zip 内のパス区切りが円記号のことがあるので末尾で照合する
                    if i.orig_filename.replace("\\", "/").endswith(suffix)
                ),
                None,
            )
            if member is None:
                raise SystemExit(f"{suffix} not found in {zip_path.name}")
            path = tmp_dir / suffix
            with zf.open(member) as src, open(path, "wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            paths[layer] = path
    return paths


def _convert(
    con: duckdb.DuckDBPyConnection,
    geojson: Path,
    parquet_path: Path,
    select: str,
) -> None:
    """GeoJSON 1 つを Parquet に変換する。

    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    con.execute(
        f"""
        COPY (
            SELECT {select} FROM ST_Read('{geojson.as_posix()}')
        ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    tmp_path.rename(parquet_path)


def _select(layer: str, pref: str) -> str:
    """医療圏の種別ごとの取り出し方。"""
    if layer == "primary":
        # ジオメトリは市区町村の区域そのものなので取り込まない。属性だけにすると
        # 行が完全に重複するため、ここで一意にしておく
        return f"""
            DISTINCT
                '{pref}' AS prefecture_code,
                A38a_001 AS admin_code,
                A38a_002 AS municipality_name,
                A38a_003 AS secondary_area_code,
                A38a_004 AS secondary_area_name,
                A38a_005 AS primary_area_setting_code
        """
    if layer == "secondary":
        return f"""
            '{pref}' AS prefecture_code,
            A38b_003 AS area_code,
            A38b_004 AS area_name,
            A38b_001 AS member_admin_codes,
            A38b_002 AS member_municipality_names,
            A38b_005 AS planned_area_km2,
            A38b_006 AS surveyed_area_km2,
            A38b_007 AS planned_population,
            A38b_008 AS population,
            A38b_009 AS population_under_15,
            A38b_010 AS population_15_to_64,
            A38b_011 AS population_65_and_over,
            ST_AsWKB(geom) AS geom
        """
    return f"""
        '{pref}' AS prefecture_code,
        A38c_002 AS area_name,
        ST_AsWKB(geom) AS geom
    """


def download_medical_area(dest_dir: str) -> None:
    """医療圏データ（一次・二次・三次）を都道府県ごとに Parquet 化する。

    都道府県ごとに zip をダウンロードして Parquet に変換し、zip は変換後すぐ
    削除する。変換済みのファイルはスキップするため、途中で中断しても再実行で
    続きから処理できる（冪等）。
    """
    dest = Path(dest_dir)
    tmp_dir = dest / "tmp"
    parquet_dirs = {layer: dest / layer for layer in LAYERS}
    for d in (tmp_dir, *parquet_dirs.values()):
        d.mkdir(parents=True, exist_ok=True)

    html = _fetch_page()
    _check_license(html)
    files = _parse_files(html)
    logger.info(f"  {len(files)} prefecture files listed")

    only = _prefectures()
    for stem, pref, url in files:
        if only is not None and pref not in only:
            continue

        targets = {
            layer: parquet_dirs[layer] / f"{stem}.parquet"
            for layer in LAYERS
            if not (parquet_dirs[layer] / f"{stem}.parquet").exists()
        }
        if not targets:
            logger.info(f"  skip {stem} (already converted)")
            continue

        zip_path = tmp_dir / f"{stem}_GML.zip"
        logger.info(f"  downloading {stem}...")
        _download(url, zip_path)

        con = duckdb.connect()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            geojson_paths = _extract(zip_path, stem, tmp_dir)
            try:
                for layer, parquet_path in targets.items():
                    _convert(
                        con, geojson_paths[layer], parquet_path, _select(layer, pref)
                    )
            finally:
                for path in geojson_paths.values():
                    path.unlink(missing_ok=True)
        finally:
            con.close()
            zip_path.unlink(missing_ok=True)

    logger.info(f"  medical area data ready in {dest}")
