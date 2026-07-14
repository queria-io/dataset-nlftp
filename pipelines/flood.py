"""国土数値情報 A31a 洪水浸水想定区域データ（河川単位）のダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から洪水浸水想定区域データ
（河川単位・2025年度）を都道府県・地方整備局等の単位でダウンロードし、
想定最大規模（L2）の GeoJSON のみを河川ごとの Parquet に変換して配置する。

全国分は zip 合計で 10GB 超・展開後はさらに大きいため、GeoJSON を
1 ファイルずつ DuckDB (spatial) で Parquet に変換し、変換後すぐ削除して
ディスク使用量を抑える。変換済み Parquet が存在するファイルはスキップ
するため、途中で中断しても再実行で続きから処理できる（冪等）。

CI (GitHub Actions) では時間・ディスクの制約からダウンロードを行わず、
初回フルビルドと年次更新はローカルで実施する（NLFTP_SKIP_FLOOD 参照）。

データソース: 洪水浸水想定区域データ（河川単位）（A31a、2025年度）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A31a-2025.html
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

# 巨大フィーチャ(利根川等)で GDAL の GeoJSON サイズ上限に当たるため無制限にする
os.environ.setdefault("OGR_GEOJSON_MAX_OBJ_SIZE", "0")

logger = logging.getLogger("pipelines")

URL_TEMPLATE = (
    "https://nlftp.mlit.go.jp/ksj/gml/data/A31a/A31a-25/"
    "A31a-25_{region}_{kind}_GEOJSON.zip"
)

# 河川種別: 10=洪水予報河川・水位周知河川, 20=その他河川
KINDS = ("10", "20")

# 地域コード: 都道府県 01〜47 と地方整備局等 81〜90（存在しないコードは 404 でスキップ）
DEFAULT_REGIONS = [f"{i:02d}" for i in range(1, 48)] + [str(i) for i in range(81, 91)]

# 想定最大規模（L2）の GeoJSON のみ取り込む。zip 内には
# 10_計画規模 / 20_想定最大規模 / 30_浸水継続時間 / 41,42_家屋倒壊等 が
# 含まれるが、ディレクトリ名の "20_" 判定は河川コードに誤爆するため、
# ファイル名プレフィックス A31a-20- で判定する。
MEMBER_PREFIX = "A31a-20-"


def flood_skipped() -> bool:
    """洪水データの取り込みをスキップするかどうか。

    NLFTP_SKIP_FLOOD=1 で明示的にスキップ、=0 で明示的に実行する。
    未指定の場合、CI (GitHub Actions) では自動的にスキップする
    （全国分のダウンロードが 10GB 超と重いため、初回フルビルドと
    年次更新はローカルで実施する運用）。
    """
    flag = os.environ.get("NLFTP_SKIP_FLOOD")
    if flag is not None:
        return flag == "1"
    return os.environ.get("GITHUB_ACTIONS") == "true"


def _regions() -> list[str]:
    """処理対象の地域コード一覧。

    NLFTP_FLOOD_REGIONS（カンマ区切り、例: "13" や "13,83"）で絞り込める。
    未指定なら全国（都道府県 01〜47 + 地方整備局等 81〜90）。
    """
    env = os.environ.get("NLFTP_FLOOD_REGIONS")
    if env:
        return [r.strip() for r in env.split(",") if r.strip()]
    return DEFAULT_REGIONS


def _decode_member_name(name: str) -> str:
    """zip 内のファイル名を CP932 として復元する。

    A31a の zip はファイル名が CP932 でエンコードされているため、
    Python zipfile が CP437 として解釈した文字列を元に戻す。
    復元できない場合はそのまま返す。
    """
    try:
        return name.encode("cp437").decode("cp932")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def _url_exists(url: str) -> bool:
    """HEAD リクエストで URL の存在を確認する（404 は False）。"""
    req = Request(url, method="HEAD", headers={"User-Agent": "dataset-nlftp"})
    try:
        with urlopen(req):
            return True
    except HTTPError as e:
        if e.code == 404:
            return False
        raise


def _convert_geojson(
    con: duckdb.DuckDBPyConnection,
    geojson_path: Path,
    parquet_path: Path,
    region: str,
) -> None:
    """GeoJSON 1 ファイルを Parquet に変換する。

    ジオメトリは WKB (BLOB) で保存し、dbt 側で ST_GeomFromWKB で復元する。
    一時ファイルに書き出してからリネームすることで、中断時に不完全な
    Parquet が変換済みとして残らないようにする。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    try:
        con.execute(
            f"""
            COPY (
                SELECT
                    '{region}' AS region_code,
                    A31a_201 AS river_code,
                    A31a_202 AS river_name,
                    A31a_203 AS admin_code,
                    A31a_204 AS admin_name,
                    A31a_205 AS depth_rank,
                    ST_AsWKB(geom) AS geom
                FROM ST_Read('{geojson_path.as_posix()}')
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    except duckdb.IOException as exc:
        if "too complex/large" not in str(exc):
            raise
        # GDAL の GeoJSON フィーチャサイズ上限(約30MB)を超える巨大ポリゴンは
        # JSON リーダー経由で変換する(遅いが上限がない)
        logger.info(f"    fallback to read_json: {geojson_path.name}")
        con.execute(
            f"""
            COPY (
                SELECT
                    '{region}' AS region_code,
                    f.properties.A31a_201 AS river_code,
                    f.properties.A31a_202 AS river_name,
                    f.properties.A31a_203 AS admin_code,
                    f.properties.A31a_204 AS admin_name,
                    f.properties.A31a_205 AS depth_rank,
                    ST_AsWKB(ST_GeomFromGeoJSON(to_json(f.geometry))) AS geom
                FROM (
                    SELECT UNNEST(features) AS f
                    FROM read_json(
                        '{geojson_path.as_posix()}',
                        maximum_object_size = 2147483647
                    )
                )
            ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    tmp_path.rename(parquet_path)


def _process_zip(
    con: duckdb.DuckDBPyConnection,
    zip_path: Path,
    parquet_dir: Path,
    tmp_dir: Path,
    region: str,
    kind: str,
) -> int:
    """zip 内の想定最大規模 GeoJSON を 1 ファイルずつ Parquet に変換する。

    710MB 超の GeoJSON を含む zip があるため、一括展開はせず 1 ファイルずつ
    取り出して変換し、即座に削除する。変換済み Parquet はスキップする。
    """
    converted = 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            decoded = _decode_member_name(info.filename)
            basename = decoded.replace("\\", "/").rsplit("/", 1)[-1]
            if not (
                basename.startswith(MEMBER_PREFIX) and basename.endswith(".geojson")
            ):
                continue

            stem = re.sub(r"[^0-9A-Za-z_.-]", "_", basename.removesuffix(".geojson"))
            parquet_path = parquet_dir / f"{region}_{kind}_{stem}.parquet"
            if parquet_path.exists():
                continue

            geojson_path = tmp_dir / "current.geojson"
            with zf.open(info) as src, open(geojson_path, "wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            try:
                _convert_geojson(con, geojson_path, parquet_path, region)
            finally:
                geojson_path.unlink(missing_ok=True)
            converted += 1
    return converted


def download_flood(dest_dir: str) -> None:
    """洪水浸水想定区域データ（想定最大規模）をダウンロードし Parquet 化する。

    地域コード×河川種別ごとに zip をダウンロードし、想定最大規模の GeoJSON を
    河川ごとの Parquet に変換する。zip・GeoJSON は変換後すぐ削除する。
    処理済みの地域はマーカーファイルでスキップする（リラン安全）。
    """
    if flood_skipped():
        logger.info("  skip (NLFTP_SKIP_FLOOD)")
        return

    dest = Path(dest_dir)
    parquet_dir = dest / "parquet"
    tmp_dir = dest / "tmp"
    done_dir = dest / ".done"
    for d in (parquet_dir, tmp_dir, done_dir):
        d.mkdir(parents=True, exist_ok=True)

    for region in _regions():
        for kind in KINDS:
            done_marker = done_dir / f"{region}_{kind}"
            if done_marker.exists():
                logger.info(f"  skip A31a-25_{region}_{kind} (done)")
                continue

            url = URL_TEMPLATE.format(region=region, kind=kind)
            if not _url_exists(url):
                logger.info(f"  skip A31a-25_{region}_{kind} (not found)")
                continue

            zip_path = tmp_dir / f"A31a-25_{region}_{kind}_GEOJSON.zip"
            logger.info(f"  downloading A31a-25_{region}_{kind}...")
            req = Request(url, headers={"User-Agent": "dataset-nlftp"})
            with urlopen(req) as resp, open(zip_path, "wb") as f:
                shutil.copyfileobj(resp, f, 1024 * 1024)

            con = duckdb.connect()
            try:
                con.execute("INSTALL spatial; LOAD spatial;")
                converted = _process_zip(
                    con, zip_path, parquet_dir, tmp_dir, region, kind
                )
            finally:
                con.close()
                zip_path.unlink(missing_ok=True)

            done_marker.touch()
            logger.info(f"  A31a-25_{region}_{kind}: {converted} files converted")

    logger.info(f"  flood inundation data ready in {parquet_dir}")
