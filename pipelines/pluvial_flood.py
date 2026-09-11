"""国土数値情報 A51 雨水出水（内水）浸水想定区域データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から雨水出水（内水）浸水想定区域
データを都道府県単位でダウンロードし、Parquet に変換して配置する。水防法に
基づいて市町村等が設定した内水氾濫の浸水想定を、浸水深の区分ごとのポリゴンと
して整備したもの。河川の氾濫（A31a）とは原因も対象範囲も違う。

利用条件
--------
このデータの使用許諾条件は全国一律で「オープンデータ（CC_BY_4.0）」であり、
高潮（A49）や津波（A40）のような都道府県別の区分は無い。都道府県ごとの
利用条件表も無いため、取り込み範囲を利用条件で絞る処理は持たない。

配布ファイルの形式
------------------
zip は都道府県単位で、中に市区町村コードのディレクトリが並び、市区町村ごとに
GeoJSON・シェープファイル・GML が入る。GeoJSON を使う。zip 内のディレクトリ名は
CP932 で入ることがあるので、拡張子の判定だけで対象を選ぶ。

配布一覧には過年度の配布分も並ぶが、新しい配布年度の zip は過年度分を含んだ
最新の状態で、同じ市区町村のファイルがそのまま入っている（2024年度配布と
2025年度配布で埼玉県川越市の GeoJSON は 36,189 地物で一致する）。
そのため都道府県ごとに最新の配布年度だけを取り込む。
整備年度は zip 内のファイル名（A51-24_11201.geojson なら2024年度）から取り、
市区町村ごとに持つ。

データソース: 雨水出水（内水）浸水想定区域（A51、2025年度版）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A51-2025.html
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

# 配布ページはデータ基準年度ごとに新設される。新しい年度が出ても既存のページには
# 追記されないので、年次更新のときはここを新しい年度のページに差し替える
PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A51-2025.html"

# 配布ページのパース結果が壊れていないことを確かめる下限
# （2025年度版時点で配布は22都道府県、過年度の配布分を含めて30ファイル）
MIN_PREFECTURES = 15


def _prefectures() -> set[str] | None:
    """処理対象を絞る都道府県コード。

    NLFTP_PLUVIAL_FLOOD_PREFECTURES（カンマ区切り、例: "02,13"）で絞り込める。
    未指定なら配布されているすべての都道府県。
    """
    env = os.environ.get("NLFTP_PLUVIAL_FLOOD_PREFECTURES")
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


def _parse_files(html: str) -> list[tuple[str, str, str]]:
    """ダウンロード一覧から (ファイル名, 都道府県コード, URL) を取り出す。

    一覧には過年度の配布分も並ぶ。都道府県ごとに最新の配布年度だけを残す。
    都道府県は一覧のラベルではなくファイル名から取る（一覧のラベルと
    ファイル名が食い違っている行があるため）。
    """
    latest: dict[str, tuple[int, str, str]] = {}
    for path in re.findall(r"DownLd\([^)]*'((?:\.\./)?data/A51/[^']+\.zip)'", html):
        url = urljoin(PAGE_URL, path)
        stem = url.rsplit("/", 1)[-1].removesuffix("_GML.zip")
        match = re.fullmatch(r"A51-(\d{2})_(\d{2})", stem)
        if not match:
            continue
        year, pref = 2000 + int(match.group(1)), match.group(2)
        if pref not in latest or year > latest[pref][0]:
            latest[pref] = (year, stem, url)
    return sorted((stem, pref, url) for pref, (_, stem, url) in latest.items())


def _drop_superseded(parquet_dir: Path, pref: str, keep: Path) -> None:
    """同じ都道府県の古い配布年度の Parquet を消す。

    新しい配布年度の zip は過年度分の市区町村ファイルをそのまま含むので、
    配布年度をまたいだ Parquet が並ぶと同じ市区町村・同じ整備年度の行が
    二重になる。配布ページの版を上げて data/ を消さずに回したときのために、
    残すもの以外をここで落とす。
    """
    for path in parquet_dir.glob(f"A51-??_{pref}.parquet"):
        if path != keep:
            logger.info(f"  removing superseded {path.name}")
            path.unlink()


def _convert(
    con: duckdb.DuckDBPyConnection,
    zip_path: Path,
    tmp_dir: Path,
    parquet_path: Path,
) -> None:
    """zip 1 つを Parquet に変換する。

    市区町村ごとに分かれた GeoJSON をすべて読んでまとめる。都道府県・市区町村は
    属性（A51_002 / A51_004）が持っているのでファイル名からは取らず、整備年度
    だけをファイル名から取る。ジオメトリは WKB (BLOB) で保存し、dbt 側で
    ST_GeomFromWKB で復元する。一時ファイルに書き出してからリネームすることで、
    中断時に不完全な Parquet が変換済みとして残らないようにする。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    extracted: list[tuple[Path, int]] = []
    with zipfile.ZipFile(zip_path) as zf:
        # ディレクトリ名は CP932 で入るが、拡張子の判定は ASCII の範囲で足りる
        members = [
            i
            for i in zf.infolist()
            if not i.is_dir() and i.filename.lower().endswith(".geojson")
        ]
        if not members:
            raise SystemExit(f"geojson not found in {zip_path.name}")
        for index, info in enumerate(members):
            name = info.filename.replace("\\", "/").rsplit("/", 1)[-1]
            match = re.fullmatch(r"A51-(\d{2})_\d{5}\.geojson", name)
            if not match:
                raise SystemExit(f"unexpected geojson name in {zip_path.name}: {name}")
            path = tmp_dir / f"current-{index}.geojson"
            with zf.open(info) as src, open(path, "wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            extracted.append((path, 2000 + int(match.group(1))))

    union = "\nUNION ALL\n".join(
        f"SELECT {year} AS data_year, A51_002 AS prefecture_code, "
        f"A51_004 AS admin_code, A51_003 AS municipality_name, "
        f"A51_005 AS depth_label, ST_AsWKB(geom) AS geom "
        f"FROM ST_Read('{path.as_posix()}')"
        for path, year in extracted
    )
    try:
        con.execute(
            f"COPY ({union}) TO '{tmp_path.as_posix()}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        for path, _ in extracted:
            path.unlink(missing_ok=True)
    tmp_path.rename(parquet_path)


def download_pluvial_flood(dest_dir: str) -> None:
    """雨水出水（内水）浸水想定区域データを Parquet 化する。

    都道府県ごとに zip をダウンロードして Parquet に変換し、zip は変換後すぐ
    削除する。変換済みのファイルはスキップするため、途中で中断しても再実行で
    続きから処理できる（冪等）。
    """
    dest = Path(dest_dir)
    parquet_dir = dest / "parquet"
    tmp_dir = dest / "tmp"
    for d in (parquet_dir, tmp_dir):
        d.mkdir(parents=True, exist_ok=True)

    files = _parse_files(_fetch_page())
    if len(files) < MIN_PREFECTURES:
        raise SystemExit(f"download list parse looks broken: {len(files)} prefectures")
    logger.info(f"  {len(files)} prefectures listed")

    only = _prefectures()
    for stem, pref, url in files:
        if only is not None and pref not in only:
            continue

        parquet_path = parquet_dir / f"{stem}.parquet"
        if parquet_path.exists():
            logger.info(f"  skip {stem} (already converted)")
            _drop_superseded(parquet_dir, pref, parquet_path)
            continue

        zip_path = tmp_dir / f"{stem}_GML.zip"
        logger.info(f"  downloading {stem}...")
        _download(url, zip_path)

        con = duckdb.connect()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            _convert(con, zip_path, tmp_dir, parquet_path)
        finally:
            con.close()
            zip_path.unlink(missing_ok=True)
        _drop_superseded(parquet_dir, pref, parquet_path)

    logger.info(f"  pluvial flood inundation data ready in {parquet_dir}")
