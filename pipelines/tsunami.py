"""国土数値情報 A40 津波浸水想定データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から津波浸水想定データを
都道府県・整備年度の単位でダウンロードし、Parquet に変換して配置する。
津波防災地域づくり法に基づき都道府県が設定した浸水想定を、浸水深の
区分ごとのポリゴンとして整備したもの。

利用条件による絞り込み
----------------------
津波浸水想定データは原典資料を作成した都道府県ごとに利用条件が異なる。
配布ページの「このデータの使用許諾条件」では

  1. オープンデータとして利用可（商用利用可・再配信可）
  2. 条件付公開（原則として商用利用可・再配信可）
  3. 条件付公開（原則として商用利用不可・再配信可）
  4. 国土数値情報としてダウンロード提供不可

の区分が示されている。ここでは 1 の都道府県のみを取り込む（2 は事前連絡や
個別の利用規約の遵守が条件に付き、3 は商用利用不可）。判定は配布ページを
毎回取得して行い、区分の記載を読み取れない場合はエラーで停止する。

配布ファイルの形式
------------------
zip には GeoJSON・シェープファイル・GML が入るが、GeoJSON は
平成29年度以降の整備分にしか無い。GeoJSON が無い zip では
シェープファイルから読む。属性を持つ .dbf は CP932 で、そのまま
読ませると文字化けするため、幾何は .shp から・属性は .dbf を
自前でデコードして読み、レコード順で突き合わせる。

データソース: 津波浸水想定（A40、第2.1版）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A40-v2_1.html
"""

import logging
import os
import re
import shutil
import struct
import zipfile
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import duckdb

logger = logging.getLogger("pipelines")

PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A40-v2_1.html"

# 使用許諾条件の区分（配布ページの見出しの記載順）
DISCLOSURE_SECTIONS = (
    (1, "オープンデータとして利用可（商用利用可・再配信可）"),
    (2, "条件付公開（原則として商用利用可・再配信可）"),
    (3, "条件付公開（原則として商用利用不可・再配信可）"),
    (4, "国土数値情報としてダウンロード提供不可"),
)
DISCLOSURE_LABELS = dict(DISCLOSURE_SECTIONS)
OPEN_CATEGORY = 1

# 配布ページのパース結果が壊れていないことを確かめる下限
# （第2.1版時点で設定済みは37道府県・うちオープンデータ利用可は28、
#   ダウンロードできるファイルは過年度整備分を含めて44）
MIN_OPEN_PREFECTURES = 20
MIN_FILES = 30

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

    NLFTP_TSUNAMI_PREFECTURES（カンマ区切り、例: "06,28"）で絞り込める。
    未指定なら利用条件で許された都道府県すべて。
    """
    env = os.environ.get("NLFTP_TSUNAMI_PREFECTURES")
    if not env:
        return None
    return {p.strip() for p in env.split(",") if p.strip()}


def _download(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "dataset-nlftp"})
    with urlopen(req) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f, 1024 * 1024)


def _fetch_page() -> str:
    """配布ページの HTML を取得する（HTML コメントは落とす）。

    コメントアウトされた記載（過去の但し書きが残っている）を利用条件の
    判定に拾わないようにする。
    """
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

    一覧には過年度整備分も並ぶ。提供元は「過年度整備分と合わせて利用し、
    重複する箇所は最新年度を使う」としているため、ここでは年度で絞らず
    すべて取り込む（重複の除外は mart 側で行う）。
    """
    files = []
    seen = set()
    for path in re.findall(r"DownLd\([^)]*'((?:\.\./)?data/A40/[^']+\.zip)'", html):
        url = urljoin(PAGE_URL, path)
        stem = url.rsplit("/", 1)[-1].removesuffix("_GML.zip")
        match = re.fullmatch(r"A40-(\d{2})_(\d{2})", stem)
        if not match or stem in seen:
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


def _decode_member_name(name: str) -> str:
    """zip 内のファイル名を CP932 として復元する。

    A40 の zip はファイル名が CP932 でエンコードされているものがあるため、
    Python zipfile が CP437 として解釈した文字列を元に戻す。
    復元できない場合はそのまま返す。
    """
    try:
        return name.encode("cp437").decode("cp932")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def _extract(zf: zipfile.ZipFile, info: zipfile.ZipInfo, dest: Path) -> None:
    with zf.open(info) as src, open(dest, "wb") as dst:
        shutil.copyfileobj(src, dst, 1024 * 1024)


def _read_dbf_column(data: bytes, column: str) -> list[str]:
    """CP932 の .dbf から 1 列をレコード順に読み出す。

    DuckDB の ST_Read はシェープファイルの .dbf を CP932 として解釈できず
    読み込みごと失敗するため、属性だけ自前で読む。
    """
    record_count, header_length, record_length = struct.unpack("<IHH", data[4:12])

    fields: list[tuple[str, int]] = []
    offset = 32
    while data[offset : offset + 1] not in (b"\x0d", b""):
        descriptor = data[offset : offset + 32]
        name = descriptor[0:11].split(b"\x00")[0].decode("ascii")
        fields.append((name, descriptor[16]))
        offset += 32

    start = 1
    for name, size in fields:
        if name == column:
            break
        start += size
    else:
        raise SystemExit(f"column {column} not found in dbf: {[f[0] for f in fields]}")

    values = []
    for i in range(record_count):
        record = data[header_length + i * record_length :][:record_length]
        values.append(record[start : start + size].decode("cp932").strip())
    return values


def _copy_geojson(
    con: duckdb.DuckDBPyConnection,
    geojson_path: Path,
    tmp_path: Path,
    pref: str,
    year: int,
) -> None:
    con.execute(
        f"""
        COPY (
            SELECT
                '{pref}' AS prefecture_code,
                {year} AS data_year,
                A40_003 AS depth_label,
                ST_AsWKB(geom) AS geom
            FROM ST_Read('{geojson_path.as_posix()}')
        ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )


def _copy_shapefile(
    con: duckdb.DuckDBPyConnection,
    shp_path: Path,
    labels: list[str],
    tmp_path: Path,
    pref: str,
    year: int,
) -> None:
    """幾何（.shp）と属性（.dbf 由来）をレコード順で突き合わせて書き出す。

    ST_Read が返す OGC_FID はシェープファイルのレコード番号（0 始まり）で、
    .dbf のレコード順と一致する。件数が食い違うときは対応が取れないので止める。
    """
    (count,) = con.execute(
        f"SELECT count(*) FROM ST_Read('{shp_path.as_posix()}')"
    ).fetchone()
    if count != len(labels):
        raise SystemExit(
            f"shapefile/dbf record mismatch: {count} shapes / {len(labels)} attributes"
        )

    con.execute("CREATE OR REPLACE TEMP TABLE attributes (fid BIGINT, label VARCHAR)")
    con.executemany("INSERT INTO attributes VALUES (?, ?)", list(enumerate(labels)))
    con.execute(
        f"""
        COPY (
            SELECT
                '{pref}' AS prefecture_code,
                {year} AS data_year,
                a.label AS depth_label,
                ST_AsWKB(s.geom) AS geom
            FROM ST_Read('{shp_path.as_posix()}') AS s
            JOIN attributes AS a ON a.fid = s.OGC_FID
        ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )


def _convert(
    con: duckdb.DuckDBPyConnection,
    zip_path: Path,
    tmp_dir: Path,
    parquet_path: Path,
    pref: str,
    year: int,
) -> None:
    """zip 1 つを Parquet に変換する。

    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path) as zf:
        members = {}
        for info in zf.infolist():
            if info.is_dir():
                continue
            decoded = _decode_member_name(info.filename).replace("\\", "/")
            members[decoded.rsplit("/", 1)[-1]] = info
        geojson = next((n for n in members if n.lower().endswith(".geojson")), None)
        if geojson:
            geojson_path = tmp_dir / "current.geojson"
            _extract(zf, members[geojson], geojson_path)
            try:
                _copy_geojson(con, geojson_path, tmp_path, pref, year)
            finally:
                geojson_path.unlink(missing_ok=True)
            tmp_path.rename(parquet_path)
            return

        # GeoJSON が無い整備年度はシェープファイルから読む。.dbf は
        # ST_Read に渡さず自前でデコードするため展開しない
        shp = next((n for n in members if n.lower().endswith(".shp")), None)
        dbf = next((n for n in members if n.lower().endswith(".dbf")), None)
        if not shp or not dbf:
            raise SystemExit(f"neither geojson nor shapefile found in {zip_path.name}")

        stem = shp.removesuffix(".shp")
        for suffix in (".shp", ".shx", ".prj"):
            member = members.get(stem + suffix)
            if member is None:
                continue
            path = tmp_dir / f"current{suffix}"
            _extract(zf, member, path)
            extracted.append(path)
        with zf.open(members[dbf]) as f:
            labels = _read_dbf_column(f.read(), "A40_003")

    try:
        _copy_shapefile(con, tmp_dir / "current.shp", labels, tmp_path, pref, year)
    finally:
        for path in extracted:
            path.unlink(missing_ok=True)
    tmp_path.rename(parquet_path)


def download_tsunami(dest_dir: str) -> None:
    """津波浸水想定データ（オープンデータ利用可の都道府県のみ）を Parquet 化する。

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

    logger.info(f"  tsunami inundation data ready in {parquet_dir}")
