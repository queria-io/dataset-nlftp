"""国土数値情報 A49 高潮浸水想定区域データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から高潮浸水想定区域データを
都道府県・整備年度の単位でダウンロードし、Parquet に変換して配置する。
水防法に基づき都道府県が設定した高潮の浸水想定を、浸水深の区分ごとの
ポリゴンとして整備したもの。

利用条件による絞り込み
----------------------
高潮浸水想定区域データは原典資料を作成した都道府県ごとに利用条件が異なる。
配布ページの「このデータの使用許諾条件」では

  1. オープンデータとして利用可（商用利用可・再配信可）
  2. 条件付き公開（原則として商用利用可・再配信可）

の区分が示されている。ここでは 1 の都道府県のみを取り込む（2 は都道府県が
公開する説明資料の確認が条件に付く）。判定は配布ページを毎回取得して行い、
区分の記載を読み取れない場合はエラーで停止する。高潮浸水想定区域を設定して
いるのは沿岸の一部の都道府県だけなので、区分に現れない都道府県がある。

配布ファイルの形式
------------------
zip には GeoJSON・シェープファイル・GML が入る。GeoJSON はすべての整備年度に
あるのでこれを使う。整備年度が古いものは沿岸（海域）ごとにファイルが分かれて
サブディレクトリに入るため、zip 内の GeoJSON をすべて読んで 1 つにまとめる。

データソース: 高潮浸水想定区域（A49、2024年度版）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A49-2024.html
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
PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A49-2024.html"

# 使用許諾条件の区分（配布ページの見出しの記載順）
DISCLOSURE_SECTIONS = (
    (1, "オープンデータとして利用可（商用利用可・再配信可）"),
    (2, "条件付き公開（原則として商用利用可・再配信可）"),
)
DISCLOSURE_LABELS = dict(DISCLOSURE_SECTIONS)
OPEN_CATEGORY = 1

# 配布ページのパース結果が壊れていないことを確かめる下限
# （2024年度版時点で区分の記載があるのは15都府県・うちオープンデータ利用可は14、
#   ダウンロードできるファイルは過年度整備分を含めて20）
MIN_OPEN_PREFECTURES = 10
MIN_FILES = 15

PREFECTURE_CODES = {
    "北海道": "01",
    "青森県": "02",
    "岩手県": "03",
    "宮城県": "04",
    "秋田県": "05",
    "山形県": "06",
    "福島県": "07",
    "茨城県": "08",
    "栃木県": "09",
    "群馬県": "10",
    "埼玉県": "11",
    "千葉県": "12",
    "東京都": "13",
    "神奈川県": "14",
    "新潟県": "15",
    "富山県": "16",
    "石川県": "17",
    "福井県": "18",
    "山梨県": "19",
    "長野県": "20",
    "岐阜県": "21",
    "静岡県": "22",
    "愛知県": "23",
    "三重県": "24",
    "滋賀県": "25",
    "京都府": "26",
    "大阪府": "27",
    "兵庫県": "28",
    "奈良県": "29",
    "和歌山県": "30",
    "鳥取県": "31",
    "島根県": "32",
    "岡山県": "33",
    "広島県": "34",
    "山口県": "35",
    "徳島県": "36",
    "香川県": "37",
    "愛媛県": "38",
    "高知県": "39",
    "福岡県": "40",
    "佐賀県": "41",
    "長崎県": "42",
    "熊本県": "43",
    "大分県": "44",
    "宮崎県": "45",
    "鹿児島県": "46",
    "沖縄県": "47",
}


def _prefectures() -> set[str] | None:
    """処理対象を絞る都道府県コード。

    NLFTP_STORM_SURGE_PREFECTURES（カンマ区切り、例: "02,36"）で絞り込める。
    未指定なら利用条件で許された都道府県すべて。
    """
    env = os.environ.get("NLFTP_STORM_SURGE_PREFECTURES")
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


def _parse_disclosure(html: str) -> dict[str, int]:
    """使用許諾条件の記載を都道府県コード → 区分の辞書にする。

    記載は 1 つの表のセルにまとまっている。そのセルを区分の見出しで区切り、
    各区分に名前が現れた都道府県を割り当てる。ページの他の場所（ダウンロード
    一覧）にも都道府県名が並ぶので、セルの外は見ない。
    """
    positions = []
    for category, heading in DISCLOSURE_SECTIONS:
        index = html.find(f"＜{heading}＞")
        if index < 0:
            raise SystemExit(f"disclosure heading not found: {heading}")
        positions.append((index, category))
    positions.sort()

    cell_end = html.find("</td>", positions[-1][0])
    if cell_end < 0:
        raise SystemExit("end of the disclosure terms cell not found")

    categories: dict[str, int] = {}
    for i, (start, category) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else cell_end
        section = html[start:end]
        for name, code in PREFECTURE_CODES.items():
            if name in section:
                categories[code] = category
    return categories


def _parse_files(html: str) -> list[tuple[str, str, int, str]]:
    """ダウンロード一覧から (ファイル名, 都道府県コード, 整備年度, URL) を取り出す。

    一覧には過年度整備分も並ぶ。年度で絞らずすべて取り込み、どの年度を公開するかは
    mart 側で決める。公開されない年度も raw に残るので、提供元の統合の注記が実態と
    合わなかった場合に取り直さずに mart だけで直せる。
    """
    files = []
    seen = set()
    codes = set(PREFECTURE_CODES.values())
    for path in re.findall(r"DownLd\([^)]*'((?:\.\./)?data/A49/[^']+\.zip)'", html):
        url = urljoin(PAGE_URL, path)
        stem = url.rsplit("/", 1)[-1].removesuffix("_GML.zip")
        match = re.fullmatch(r"A49-(\d{2})_(\d{2})", stem)
        if not match or match.group(2) not in codes or stem in seen:
            continue
        seen.add(stem)
        files.append((stem, match.group(2), 2000 + int(match.group(1)), url))
    return sorted(files)


def _write_license(dest: Path, categories: dict[str, int]) -> None:
    """都道府県別の利用条件区分を Parquet に書き出す。"""
    con = duckdb.connect()
    try:
        con.execute(
            "CREATE TEMP TABLE license (prefecture_code VARCHAR, "
            "disclosure_category INTEGER, disclosure_label VARCHAR)"
        )
        con.executemany(
            "INSERT INTO license VALUES (?, ?, ?)",
            [
                (code, category, DISCLOSURE_LABELS[category])
                for code, category in sorted(categories.items())
            ],
        )
        con.execute(
            f"COPY license TO '{(dest / 'license.parquet').as_posix()}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        con.close()


def _convert(
    con: duckdb.DuckDBPyConnection,
    zip_path: Path,
    tmp_dir: Path,
    parquet_path: Path,
    pref: str,
    year: int,
) -> None:
    """zip 1 つを Parquet に変換する。

    沿岸ごとに分かれた GeoJSON をすべて読んでまとめる。ジオメトリは WKB (BLOB)
    で保存し、dbt 側で ST_GeomFromWKB で復元する。一時ファイルに書き出してから
    リネームすることで、中断時に不完全な Parquet が変換済みとして残らないように
    する。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path) as zf:
        # サブディレクトリ名は CP932 で入るが、拡張子の判定は ASCII の範囲で足りる
        members = [
            i
            for i in zf.infolist()
            if not i.is_dir() and i.filename.lower().endswith(".geojson")
        ]
        if not members:
            raise SystemExit(f"geojson not found in {zip_path.name}")
        for index, info in enumerate(members):
            path = tmp_dir / f"current-{index}.geojson"
            with zf.open(info) as src, open(path, "wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            extracted.append(path)

    # 年度によって GeoJSON の属性の数が違う（FID を持つものがある）ため、
    # 使う列だけを選んで形を揃えてから結合する
    union = "\nUNION ALL\n".join(
        f"SELECT A49_003 AS depth_label, ST_AsWKB(geom) AS geom "
        f"FROM ST_Read('{path.as_posix()}')"
        for path in extracted
    )
    try:
        con.execute(
            f"""
            COPY (
                SELECT
                    '{pref}' AS prefecture_code,
                    {year} AS data_year,
                    depth_label,
                    geom
                FROM ({union})
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        for path in extracted:
            path.unlink(missing_ok=True)
    tmp_path.rename(parquet_path)


def download_storm_surge(dest_dir: str) -> None:
    """高潮浸水想定区域データ（オープンデータ利用可の都道府県のみ）を Parquet 化する。

    都道府県 × 整備年度ごとに zip をダウンロードして Parquet に変換し、
    zip は変換後すぐ削除する。変換済みのファイルはスキップするため、
    途中で中断しても再実行で続きから処理できる（冪等）。
    """
    dest = Path(dest_dir)
    parquet_dir = dest / "parquet"
    tmp_dir = dest / "tmp"
    for d in (parquet_dir, tmp_dir):
        d.mkdir(parents=True, exist_ok=True)

    html = _fetch_page()
    categories = _parse_disclosure(html)
    open_codes = {c for c, v in categories.items() if v == OPEN_CATEGORY}
    if len(open_codes) < MIN_OPEN_PREFECTURES:
        raise SystemExit(
            f"disclosure terms parse looks broken: {len(open_codes)} open prefectures"
        )
    _write_license(dest, categories)

    files = _parse_files(html)
    if len(files) < MIN_FILES:
        raise SystemExit(f"download list parse looks broken: {len(files)} files")
    logger.info(f"  {len(open_codes)} prefectures open data, {len(files)} files listed")

    only = _prefectures()
    for stem, pref, year, url in files:
        if pref not in open_codes or (only is not None and pref not in only):
            continue

        parquet_path = parquet_dir / f"{stem}.parquet"
        if parquet_path.exists():
            logger.info(f"  skip {stem} (already converted)")
            continue

        zip_path = tmp_dir / f"{stem}_GML.zip"
        logger.info(f"  downloading {stem}...")
        _download(url, zip_path)

        con = duckdb.connect()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            _convert(con, zip_path, tmp_dir, parquet_path, pref, year)
        finally:
            con.close()
            zip_path.unlink(missing_ok=True)

    logger.info(f"  storm surge inundation data ready in {parquet_dir}")
