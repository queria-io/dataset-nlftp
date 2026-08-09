"""国土数値情報 L03-b-u 都市地域土地利用細分メッシュのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から都市地域土地利用細分メッシュ
（第3.1版・令和3年度）を 1 次メッシュ単位でダウンロードし、UTF-8 の GeoJSON を
Parquet に変換して配置する。

zip 合計 300MB 超・展開後の GeoJSON は 1 ファイルで 150MB を超えるため、
1 ファイルずつ取り出して DuckDB (spatial) で Parquet に変換し、変換後すぐ削除して
ディスク使用量を抑える。変換済み Parquet が存在するメッシュはスキップするため、
途中で中断しても再実行で続きから処理できる（冪等）。

データソース: 都市地域土地利用細分メッシュデータ（L03-b-u、第3.1版・令和3年度）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-L03-b-u-v3_1.html
"""

import logging
import os
import shutil
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import duckdb

logger = logging.getLogger("pipelines")

URL_TEMPLATE = (
    "https://nlftp.mlit.go.jp/ksj/gml/data/L03-b-u/L03-b-u-21/"
    "L03-b-u-21_{mesh}-jgd2011_GML.zip"
)

# 令和3年度版が整備されている 1 次メッシュ（80km 四方）のコード。
# 整備対象は都市地域の範囲内に限られ、北海道と東北北部は対象外。
DEFAULT_MESHES = [
    "3624", "3725", "3927", "3928", "3942", "4027", "4028", "4042", "4128",
    "4129", "4229", "4530", "4630", "4631", "4730", "4731", "4828", "4829",
    "4830", "4831", "4928", "4929", "4930", "4931", "4932", "4933", "4934",
    "4939", "5029", "5030", "5031", "5032", "5033", "5034", "5035", "5036",
    "5129", "5130", "5131", "5132", "5133", "5134", "5135", "5136", "5137",
    "5138", "5139", "5231", "5232", "5233", "5234", "5235", "5236", "5237",
    "5238", "5239", "5240", "5332", "5333", "5334", "5335", "5336", "5337",
    "5338", "5339", "5340", "5433", "5436", "5437", "5438", "5439", "5440",
    "5536", "5537", "5538", "5539", "5540", "5541", "5636", "5637", "5638",
    "5639", "5738", "5739",
]


def _meshes() -> list[str]:
    """処理対象の 1 次メッシュコード一覧。

    NLFTP_LANDUSE_MESHES（カンマ区切り、例: "5339" や "5339,5340"）で絞り込める。
    未指定なら整備済みの全 84 メッシュ。
    """
    env = os.environ.get("NLFTP_LANDUSE_MESHES")
    if env:
        return [m.strip() for m in env.split(",") if m.strip()]
    return DEFAULT_MESHES


def _geojson_member(zf: zipfile.ZipFile) -> zipfile.ZipInfo:
    """zip 内の GeoJSON メンバーを 1 つ返す。

    メッシュによって zip 直下に置かれている場合とディレクトリに入っている場合が
    あり、後者は区切りがバックスラッシュのため、パス区切りを正規化して判定する。
    """
    for info in zf.infolist():
        if info.is_dir():
            continue
        basename = info.filename.replace("\\", "/").rsplit("/", 1)[-1]
        if basename.endswith(".geojson"):
            return info
    raise RuntimeError(f"geojson not found in {zf.filename}")


def _convert_geojson(
    con: duckdb.DuckDBPyConnection, geojson_path: Path, parquet_path: Path
) -> None:
    """GeoJSON 1 ファイルを Parquet に変換する。

    属性名が日本語のためここで英語の列名に直す。ジオメトリは WKB (BLOB) で保存し、
    dbt 側で ST_GeomFromWKB で復元する。一時ファイルに書き出してからリネームする
    ことで、中断時に不完全な Parquet が変換済みとして残らないようにする。
    """
    tmp_path = parquet_path.with_suffix(".parquet.tmp")
    con.execute(
        f"""
        COPY (
            SELECT
                "細分メッシュコード" AS mesh_code,
                "土地利用種別" AS landuse_code,
                "衛星写真撮影年月日" AS survey_date,
                ST_AsWKB(geom) AS geom
            FROM ST_Read('{geojson_path.as_posix()}')
        ) TO '{tmp_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    tmp_path.rename(parquet_path)


def download_landuse(dest_dir: str) -> None:
    """都市地域土地利用細分メッシュをダウンロードし Parquet 化する。

    1 次メッシュごとに zip をダウンロードして GeoJSON を Parquet に変換する。
    zip・GeoJSON は変換後すぐ削除する。変換済みのメッシュはスキップする。
    """
    dest = Path(dest_dir)
    parquet_dir = dest / "parquet"
    tmp_dir = dest / "tmp"
    for d in (parquet_dir, tmp_dir):
        d.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    try:
        con.execute("INSTALL spatial; LOAD spatial;")

        for mesh in _meshes():
            parquet_path = parquet_dir / f"L03-b-u-21_{mesh}.parquet"
            if parquet_path.exists():
                logger.info(f"  skip {mesh} (already converted)")
                continue

            zip_path = tmp_dir / f"L03-b-u-21_{mesh}.zip"
            logger.info(f"  downloading L03-b-u-21_{mesh}...")
            req = Request(
                URL_TEMPLATE.format(mesh=mesh),
                headers={"User-Agent": "dataset-nlftp"},
            )
            with urlopen(req) as resp, open(zip_path, "wb") as f:
                shutil.copyfileobj(resp, f, 1024 * 1024)

            geojson_path = tmp_dir / "current.geojson"
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    member = _geojson_member(zf)
                    with zf.open(member) as src, open(geojson_path, "wb") as dst:
                        shutil.copyfileobj(src, dst, 1024 * 1024)
                _convert_geojson(con, geojson_path, parquet_path)
            finally:
                geojson_path.unlink(missing_ok=True)
                zip_path.unlink(missing_ok=True)
    finally:
        con.close()

    logger.info(f"  landuse mesh data ready in {parquet_dir}")
