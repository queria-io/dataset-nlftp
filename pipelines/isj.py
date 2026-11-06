"""位置参照情報（街区レベル・大字・町丁目レベル）のダウンロード。

国土交通省「位置参照情報ダウンロードサービス」から、街区レベル（a）と
大字・町丁目レベル（b）の位置参照情報を都道府県単位でダウンロードし、
Parquet に変換して配置する。

配布の範囲
----------
位置参照情報利用約款により無償で利用できる。転載するときは
「街区レベル位置参照情報　国土交通省」「大字・町丁目位置参照情報　国土交通省」の
ように出典を明記する。街区レベルは都市計画区域相当の範囲だけを整備している。

配布ファイルの形式
------------------
zip には都道府県 1 ファイルの CSV（CP932、全列を二重引用符で囲む）が入る。
街区レベルの zip は CSV を直下に、大字・町丁目レベルの zip は
<都道府県コード>000-<版>/ の下に置くので、ファイル名の末尾で照合する。
CSV の列名は原典の日本語のままで Parquet にし、型と列名は dbt 側で整える。

版はデータの種類ごとに番号が別で、街区レベルの 24.0a と大字・町丁目レベルの
19.0b はどちらも令和6年度（CSV のファイル名は <都道府県コード>_2025.csv）。

街区レベルは過去の版（10.0a〜23.0a、CSV のファイル名は <都道府県コード>_2011.csv
〜_2024.csv）も block_history/ に取り込む。15.0a までは「小字・通称名」の列が無く、
「大字・町丁目名」に小字まで続けて書く版がある。列をそろえるため、その版には
空の「小字・通称名」を足す。

データソース: 位置参照情報ダウンロードサービス
https://nlftp.mlit.go.jp/isj/index.html
"""

import logging
import os
import zipfile
from pathlib import Path

import duckdb

from pipelines.download import download

logger = logging.getLogger("pipelines")

BASE_URL = "https://nlftp.mlit.go.jp/isj/dls/data"

# 取り込む版。整備年度が進むと街区レベルは 25.0a、大字・町丁目レベルは 20.0b になる
VERSIONS = {"block": "24.0a", "oaza": "19.0b"}

# CSV の先頭行。列が変わったら dbt の列名の対応も変わるので、取り込みを続けない
HEADERS = {
    "block": (
        "都道府県名,市区町村名,大字・丁目名,小字・通称名,街区符号・地番,座標系番号,"
        "Ｘ座標,Ｙ座標,緯度,経度,住居表示フラグ,代表フラグ,更新前履歴フラグ,更新後履歴フラグ"
    ),
    "oaza": (
        "都道府県コード,都道府県名,市区町村コード,市区町村名,大字町丁目コード,"
        "大字町丁目名,緯度,経度,原典資料コード,大字・字・丁目区分コード"
    ),
}

# 街区レベルの過去の版。ダウンロードできる最も古い 10.0a（平成22年度）から、VERSIONS の
# 版の 1 つ前まで。VERSIONS を新しい版にすると、それまでの版も自動でここに入る
HISTORY_VERSIONS = [f"{n}.0a" for n in range(10, int(VERSIONS["block"].split(".")[0]))]

# 15.0a までの街区レベルの先頭行（「小字・通称名」の列が無い）
OLD_BLOCK_HEADER = (
    "都道府県名,市区町村名,大字・町丁目名,街区符号・地番,座標系番号,"
    "Ｘ座標,Ｙ座標,緯度,経度,住居表示フラグ,代表フラグ,更新前履歴フラグ,更新後履歴フラグ"
)

PREFECTURE_CODES = [f"{i:02d}" for i in range(1, 48)]


def _prefectures() -> list[str]:
    """処理対象の都道府県コード。

    NLFTP_ISJ_PREFECTURES（カンマ区切り、例: "13,47"）で絞り込める。
    未指定なら全都道府県。
    """
    env = os.environ.get("NLFTP_ISJ_PREFECTURES")
    if not env:
        return PREFECTURE_CODES
    return sorted({p.strip() for p in env.split(",") if p.strip()})


def _convert(zip_path: Path, level: str, tmp_dir: Path, parquet_path: Path) -> None:
    """zip 内の CSV を UTF-8 にして Parquet に変換する。

    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    """
    with zipfile.ZipFile(zip_path) as zf:
        members = [i for i in zf.infolist() if i.filename.lower().endswith(".csv")]
        if len(members) != 1:
            raise SystemExit(f"expected 1 CSV in {zip_path.name}, found {len(members)}")
        # 原典には CP932 として読めないバイトが混ざる版がある（街区レベル 20.0a の島根県で
        # 1 か所）。その文字だけ U+FFFD にして取り込みを続ける
        text = zf.read(members[0]).decode("cp932", errors="replace")
        if (broken := text.count("\ufffd")) > 0:
            logger.warning(f"  {zip_path.name}: {broken} undecodable byte(s) replaced")

    # 列の並びが違う版がある（街区レベル 20.0a の千葉県）。列は名前で読むので、並びは問わない
    header = set(text.split("\n", 1)[0].strip().replace('"', "").split(","))
    if header == set(HEADERS[level].split(",")):
        columns = "*"
    elif level == "block" and header == set(OLD_BLOCK_HEADER.split(",")):
        # 古い版は列名を今の版にそろえ、無い小字の列を空で足す
        columns = (
            """* RENAME ("大字・町丁目名" AS "大字・丁目名"), '' AS "小字・通称名\""""
        )
    else:
        raise SystemExit(f"unexpected columns in {zip_path.name}: {header}")

    csv_path = tmp_dir / f"{parquet_path.stem}.csv"
    csv_path.write_text(text, encoding="utf-8")
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    con = duckdb.connect()
    try:
        con.execute(
            f"""
            COPY (
                SELECT {columns},
                    '{members[0].filename.replace(chr(92), "/").rsplit("/", 1)[-1]}' AS source_file
                FROM read_csv('{csv_path.as_posix()}', header = true, all_varchar = true)
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        con.close()
        csv_path.unlink(missing_ok=True)
    tmp_path.rename(parquet_path)


def _download_level(dest: Path, level: str) -> None:
    version = VERSIONS[level]
    parquet_dir = dest / level / "parquet"
    parquet_dir.mkdir(parents=True, exist_ok=True)

    # raw は parquet/*.parquet をすべて読むので、別の版の Parquet が残っていると
    # 2 つの版の行が重なる
    for stale in parquet_dir.glob("*.parquet"):
        if not stale.name.endswith(f"-{version}.parquet"):
            logger.info(f"  removing {stale.name} (not {version})")
            stale.unlink()

    _download_version(dest, level, version, parquet_dir)


def _download_version(dest: Path, level: str, version: str, parquet_dir: Path) -> None:
    tmp_dir = dest / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for pref in _prefectures():
        stem = f"{pref}000-{version}"
        parquet_path = parquet_dir / f"{stem}.parquet"
        if parquet_path.exists():
            logger.info(f"  skip {stem} (already converted)")
            continue
        zip_path = tmp_dir / f"{stem}.zip"
        logger.info(f"  downloading {stem}...")
        download(f"{BASE_URL}/{version}/{stem}.zip", zip_path)
        try:
            _convert(zip_path, level, tmp_dir, parquet_path)
        finally:
            zip_path.unlink(missing_ok=True)


def download_isj(dest_dir: str) -> None:
    """街区レベルと大字・町丁目レベルの位置参照情報、街区レベルの過去の版を Parquet 化する。

    都道府県ごとの zip をダウンロードして Parquet に変換し、zip は変換後すぐ削除する。
    変換済みならスキップする（冪等）。
    """
    dest = Path(dest_dir)
    for level in VERSIONS:
        _download_level(dest, level)
    history_dir = dest / "block_history" / "parquet"
    history_dir.mkdir(parents=True, exist_ok=True)
    for version in HISTORY_VERSIONS:
        _download_version(dest, "block", version, history_dir)
    logger.info(f"  isj data ready in {dest}")
