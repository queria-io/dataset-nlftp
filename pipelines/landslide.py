"""国土数値情報 A33 土砂災害警戒区域データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から土砂災害警戒区域データを
都道府県単位でダウンロードし、Parquet に変換して配置する。土砂災害防止法
第7条に基づき都道府県が指定した警戒区域（イエローゾーン）・特別警戒区域
（レッドゾーン）を、現象の種類ごとの区域ポリゴンとして整備したもの。

利用条件による絞り込み
----------------------
土砂災害警戒区域データは原典資料を作成した都道府県ごとに利用条件が異なる。
配布ページの「このデータの使用許諾条件」では

  1. オープンデータとしての利用可（商用利用可・再配信可）
  2. 条件付公開

の区分が示されている。ここでは 1 の都道府県のみを取り込む（2 は都道府県ごとに
定められた公開条件の確認が前提になる）。判定は配布ページを毎回取得して行い、
区分の記載を読み取れない場合はエラーで停止する。

配布ファイルの形式
------------------
2025年度版は GeoJSON・シェープファイル・GML の 3 形式で配布される。ここでは
GeoJSON を使う（シェープファイルの .dbf は CP932 で DuckDB の ST_Read が
読めない）。区域は面と線の両方で整備されるため zip に GeoJSON が 2 つ入る
ことがあり、面（`...Polygon.geojson`）だけを読む。

データソース: 土砂災害警戒区域（A33、2025年度版）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A33-2025.html
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

PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A33-2025.html"

# 取り込む整備年度（ファイル名の A33-<yy>）。過年度分も同じページに並ぶが、
# 最新年度が全都道府県を収録しているので最新年度だけを取る
FILE_PREFIX = "A33-25"

# 使用許諾条件の区分（配布ページの見出しの記載順）
DISCLOSURE_SECTIONS = (
    (1, "オープンデータとしての利用可（商用利用可・再配信可）"),
    (2, "条件付公開"),
)
DISCLOSURE_LABELS = dict(DISCLOSURE_SECTIONS)
OPEN_CATEGORY = 1

# 配布ページのパース結果が壊れていないことを確かめる下限
# （2025年度版時点でオープンデータ利用可は41都道府県）
MIN_OPEN_PREFECTURES = 30

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

    NLFTP_LANDSLIDE_PREFECTURES（カンマ区切り、例: "13,47"）で絞り込める。
    未指定なら利用条件で許された都道府県すべて。
    """
    env = os.environ.get("NLFTP_LANDSLIDE_PREFECTURES")
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

    # 全都道府県がいずれかの区分に現れるのが正しい状態。欠けているときは
    # 見出しの表記か区切りの読み取りが変わっているので、そのまま進めない
    missing = sorted(set(PREFECTURE_CODES.values()) - set(categories))
    if missing:
        raise SystemExit(f"prefectures missing from the disclosure terms: {missing}")
    return categories


def _parse_files(html: str) -> list[tuple[str, str, str]]:
    """ダウンロード一覧から (ファイル名, 都道府県コード, URL) を取り出す。

    一覧には過年度整備分と、全国・地方単位のまとめも並ぶ。最新年度の
    都道府県単位の GeoJSON だけを拾う（全国・地方のファイルは都道府県コードの
    範囲外の番号を持つので、コードの一致で落ちる）。
    """
    files = []
    seen = set()
    codes = set(PREFECTURE_CODES.values())
    for path in re.findall(r"DownLd\([^)]*'((?:\.\./)?data/A33/[^']+\.zip)'", html):
        url = urljoin(PAGE_URL, path)
        stem = url.rsplit("/", 1)[-1].removesuffix("_GEOJSON.zip")
        match = re.fullmatch(rf"{FILE_PREFIX}_(\d{{2}})", stem)
        if not match or match.group(1) not in codes or stem in seen:
            continue
        seen.add(stem)
        files.append((stem, match.group(1), url))
    if len(files) != len(codes):
        raise SystemExit(f"download list parse looks broken: {len(files)} files")
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
) -> None:
    """zip 1 つを Parquet に変換する。

    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    geojson_path = tmp_dir / "current.geojson"
    with zipfile.ZipFile(zip_path) as zf:
        # 線データの GeoJSON が同居することがある。属性の名前が面と同じで
        # そのまま読めてしまうので、面のファイルを名前で選ぶ
        member = next(
            (
                i
                for i in zf.infolist()
                if i.orig_filename.lower().endswith("polygon.geojson")
            ),
            None,
        )
        if member is None:
            raise SystemExit(f"polygon geojson not found in {zip_path.name}")
        with zf.open(member) as src, open(geojson_path, "wb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)

    try:
        con.execute(
            f"""
            COPY (
                SELECT
                    '{pref}' AS prefecture_code,
                    A33_001 AS phenomenon_code,
                    A33_002 AS zone_code,
                    A33_004 AS zone_number,
                    A33_005 AS zone_name,
                    A33_006 AS address,
                    A33_007 AS notice_date,
                    A33_008 AS special_zone_unspecified_code,
                    ST_AsWKB(geom) AS geom
                FROM ST_Read('{geojson_path.as_posix()}')
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        geojson_path.unlink(missing_ok=True)
    tmp_path.rename(parquet_path)


def download_landslide(dest_dir: str) -> None:
    """土砂災害警戒区域データ（オープンデータ利用可の都道府県のみ）を Parquet 化する。

    都道府県ごとに zip をダウンロードして Parquet に変換し、zip は変換後すぐ
    削除する。変換済みのファイルはスキップするため、途中で中断しても再実行で
    続きから処理できる（冪等）。
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
    logger.info(f"  {len(open_codes)} prefectures open data, {len(files)} files listed")

    only = _prefectures()
    for stem, pref, url in files:
        if pref not in open_codes or (only is not None and pref not in only):
            continue

        parquet_path = parquet_dir / f"{stem}.parquet"
        if parquet_path.exists():
            logger.info(f"  skip {stem} (already converted)")
            continue

        zip_path = tmp_dir / f"{stem}_GEOJSON.zip"
        logger.info(f"  downloading {stem}...")
        _download(url, zip_path)

        con = duckdb.connect()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            _convert(con, zip_path, tmp_dir, parquet_path, pref)
        finally:
            con.close()
            zip_path.unlink(missing_ok=True)

    logger.info(f"  landslide hazard area data ready in {parquet_dir}")
