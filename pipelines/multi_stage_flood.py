"""国土数値情報 A53 多段階浸水想定データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から多段階の浸水想定図を地方整備局
単位でダウンロードし、Parquet に変換して配置する。洪水浸水想定区域（A31a）が
想定最大規模降雨だけを対象にするのに対し、こちらは高頻度から中頻度の降雨規模
（1/10・1/30・1/50・1/100 と河川整備の計画規模 1/150 または 1/200）ごとに
浸水深の区分をポリゴンで持つ。

利用条件
--------
このデータの使用許諾条件は全国一律で「オープンデータ（CC_BY_4.0）」であり、
津波（A40）や高潮（A49）のような都道府県別の区分は無い。取り込み範囲を
利用条件で絞る処理は持たない。

配布ファイルの形式
------------------
zip は地方整備局等の 2 桁コード（81 北海道開発局 〜 89 九州地方整備局）単位で、
中に水系 × 降雨規模ごとの GeoJSON が並ぶ（A53-24_860602_紀の川水系_86_010.geojson
なら 2024 年度整備・水系コード 860602・降雨規模 1/10）。ファイル名の水系名と
降雨規模は属性（A53_002 / A53_005）にも入るので、ファイル名からは整備年度だけを
取る。zip 内のファイル名は CP932 で入るが、整備年度と拡張子の判定は ASCII の
範囲で足りる。

配布一覧には過年度の配布分も並ぶ。新しい配布年度の zip は過年度分を含んだ最新の
状態で、2025年度版の近畿地方整備局は 2023年度整備の 14 ファイルと 2024年度整備の
22 ファイルをそのまま含む（2023年度版 14 ファイル + 2024年度版 22 ファイルと一致）。
そのため地方整備局ごとに最新の配布年度だけを取り込む。

同じ水系コードでも対象区間が違うと別のファイルになる（淀川水系は
（桂川）（木津川上流）（木津川下流）（猪名川）に分かれる）。区間名は水系名
（A53_002）のかっこ書きに入るので、水系コードだけでは一意にならない。

展開後のサイズが大きい（北海道開発局は GeoJSON 57 ファイルで 1.6GB、最大の
1 ファイルが 381MB）ため、zip から 1 ファイルずつ取り出して Parquet に変換し、
最後に結合する。展開済みの GeoJSON を同時に抱えない。

データソース: 多段階浸水想定データ（A53、2025年度版）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A53-2025.html
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
PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A53-2025.html"

# 配布ページのパース結果が壊れていないことを確かめる下限。
# 2025年度版時点で配布は 81〜89 の 9 区分（過年度の配布分を含めて 23 ファイル）で、
# 区分あたりの偏りが大きい（北海道開発局だけで全体の 45%）。1 区分の取りこぼしで
# 4 割が欠けたまま公開まで進まないよう、判明している区分数をそのまま下限にする。
# 配布ファイル名の区切りは "_" と "-" が混ざるので、命名が変わればここで止まる
MIN_BUREAUS = 9


def _bureaus() -> set[str] | None:
    """処理対象を絞る地方整備局等コード。

    NLFTP_MULTI_STAGE_FLOOD_BUREAUS（カンマ区切り、例: "86,87"）で絞り込める。
    未指定なら配布されているすべての地方整備局等。
    """
    env = os.environ.get("NLFTP_MULTI_STAGE_FLOOD_BUREAUS")
    if not env:
        return None
    return {b.strip() for b in env.split(",") if b.strip()}


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


def _parse_files(html: str) -> list[tuple[int, str, str]]:
    """ダウンロード一覧から (配布年度, 地方整備局等コード, URL) を取り出す。

    一覧には過年度の配布分も並ぶ。地方整備局等ごとに最新の配布年度だけを残す。
    配布年度と整備局コードの区切りは配布年度によって "_" と "-" が混ざる
    （A53-25_86_GEOJSON.zip / A53-23-86_GEOJSON.zip）。
    """
    latest: dict[str, tuple[int, str]] = {}
    for path in re.findall(r"DownLd\([^)]*'([^']*/data/A53/[^']+\.zip)'", html):
        url = urljoin(PAGE_URL, path)
        stem = url.rsplit("/", 1)[-1].removesuffix("_GEOJSON.zip")
        match = re.fullmatch(r"A53-(\d{2})[-_](\d{2})", stem)
        if not match:
            continue
        year, bureau = 2000 + int(match.group(1)), match.group(2)
        if bureau not in latest or year > latest[bureau][0]:
            latest[bureau] = (year, url)
    return sorted((year, bureau, url) for bureau, (year, url) in latest.items())


def _drop_superseded(parquet_dir: Path, bureau: str, keep: Path) -> None:
    """同じ地方整備局等の古い配布年度の Parquet を消す。

    新しい配布年度の zip は過年度分のファイルをそのまま含むので、配布年度を
    またいだ Parquet が並ぶと同じ水系・同じ降雨規模の行が二重になる。配布ページの
    版を上げて data/ を消さずに回したときのために、残すもの以外をここで落とす。
    """
    for path in parquet_dir.glob(f"A53-??_{bureau}.parquet"):
        if path != keep:
            logger.info(f"  removing superseded {path.name}")
            path.unlink()


def _convert(
    con: duckdb.DuckDBPyConnection,
    zip_path: Path,
    bureau: str,
    tmp_dir: Path,
    parquet_path: Path,
) -> None:
    """zip 1 つを Parquet に変換する。

    展開後の GeoJSON が大きいので、1 ファイルずつ取り出して Parquet の断片に
    変換し、GeoJSON をその場で捨てる。最後に断片を 1 ファイルへ結合する。
    水系・降雨規模・浸水深ランクは属性が持っているのでファイル名からは取らず、
    整備年度をファイル名から、地方整備局等コードを zip の配布単位から取る。
    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な Parquet が
    変換済みとして残らないようにする。

    断片は結合したら消すが、強制終了で消し損ねた断片が残っていると次の配布単位の
    Parquet に混ざる。zip を開く前に残骸を落としてから始める。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    for stale in list(tmp_dir.glob("part-*.parquet")) + list(
        tmp_dir.glob("current-*.geojson")
    ):
        stale.unlink(missing_ok=True)
    parts: list[Path] = []
    try:
        with zipfile.ZipFile(zip_path) as zf:
            # ディレクトリ名は CP932 で入るが、整備年度と拡張子は ASCII の範囲
            members = [
                i
                for i in zf.infolist()
                if not i.is_dir() and i.filename.lower().endswith(".geojson")
            ]
            if not members:
                raise SystemExit(f"geojson not found in {zip_path.name}")
            for index, info in enumerate(members):
                name = info.filename.replace("\\", "/").rsplit("/", 1)[-1]
                match = re.match(r"A53-(\d{2})_", name)
                if not match:
                    raise SystemExit(
                        f"unexpected geojson name in {zip_path.name}: {name}"
                    )
                year = 2000 + int(match.group(1))

                geojson_path = tmp_dir / f"current-{index}.geojson"
                part_path = tmp_dir / f"part-{index}.parquet"
                with zf.open(info) as src, open(geojson_path, "wb") as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
                try:
                    con.execute(
                        f"COPY (SELECT {year} AS data_year, "
                        f"'{bureau}' AS bureau_code, "
                        "A53_001 AS river_system_code, "
                        "A53_002 AS river_system_name, "
                        "A53_003 AS depth_rank_3, A53_004 AS depth_rank_6, "
                        "A53_005 AS rainfall_probability_denominator, "
                        "ST_AsWKB(geom) AS geom "
                        f"FROM ST_Read('{geojson_path.as_posix()}')) "
                        f"TO '{part_path.as_posix()}' "
                        "(FORMAT PARQUET, COMPRESSION ZSTD)"
                    )
                finally:
                    geojson_path.unlink(missing_ok=True)
                parts.append(part_path)

        glob = (tmp_dir / "part-*.parquet").as_posix()
        con.execute(
            f"COPY (SELECT * FROM read_parquet('{glob}')) TO '{tmp_path.as_posix()}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        for path in parts:
            path.unlink(missing_ok=True)
    tmp_path.rename(parquet_path)


def download_multi_stage_flood(dest_dir: str) -> None:
    """多段階浸水想定データを Parquet 化する。

    地方整備局等ごとに zip をダウンロードして Parquet に変換し、zip は変換後すぐ
    削除する。変換済みのファイルはスキップするため、途中で中断しても再実行で
    続きから処理できる（冪等）。
    """
    dest = Path(dest_dir)
    parquet_dir = dest / "parquet"
    tmp_dir = dest / "tmp"
    for d in (parquet_dir, tmp_dir):
        d.mkdir(parents=True, exist_ok=True)

    files = _parse_files(_fetch_page())
    if len(files) < MIN_BUREAUS:
        raise SystemExit(f"download list parse looks broken: {len(files)} bureaus")
    logger.info(f"  {len(files)} bureaus listed")

    only = _bureaus()
    for year, bureau, url in files:
        if only is not None and bureau not in only:
            continue

        # 配布ファイル名の区切りは年度によって揺れるので、Parquet 側は
        # A53-<配布年度下2桁>_<整備局コード>.parquet に揃える
        name = f"A53-{year % 100:02d}_{bureau}"
        parquet_path = parquet_dir / f"{name}.parquet"
        if parquet_path.exists():
            logger.info(f"  skip {name} (already converted)")
            _drop_superseded(parquet_dir, bureau, parquet_path)
            continue

        zip_path = tmp_dir / f"{name}_GEOJSON.zip"
        logger.info(f"  downloading {name}...")
        _download(url, zip_path)

        con = duckdb.connect()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            _convert(con, zip_path, bureau, tmp_dir, parquet_path)
        finally:
            con.close()
            zip_path.unlink(missing_ok=True)
        _drop_superseded(parquet_dir, bureau, parquet_path)

    logger.info(f"  multi stage flood inundation data ready in {parquet_dir}")
