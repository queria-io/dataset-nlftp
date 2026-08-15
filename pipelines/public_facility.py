"""国土数値情報 P05 市町村役場等及び公的集会施設データのダウンロード。

国土交通省「国土数値情報ダウンロードサイト」から市町村役場等及び公的集会施設
データ（本庁・支所・行政サービス施設・公立公民館・集会施設のポイント）を
ダウンロードし展開する。全国版の zip は 47 都道府県分の zip を束ねた入れ子構造
なので、内側の zip に同梱される UTF-8 の GeoJSON を 1 つの FeatureCollection に
統合する。zip には Shift-JIS の Shapefile も含まれるが、文字化けを避けて
GeoJSON のみを使う。

データソース: 市町村役場等及び公的集会施設データ（2022年（令和4年）版）
https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P05-2022.html
"""

import io
import json
import logging
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

URL = "https://nlftp.mlit.go.jp/ksj/gml/data/P05/P05-22/P05-22_GML.zip"

# 都道府県コード 01〜47。全国版 zip には地方ブロック単位の zip も並ぶ配布形態が
# あるため、拾うメンバーを都道府県分だけに固定して二重計上と取りこぼしを防ぐ
PREF_CODES = range(1, 48)

# 統合後の GeoJSON（raw モデルが ST_Read で読む単一ファイル）
MERGED_GEOJSON = "P05-22.geojson"


def download_public_facility(dest_dir: str) -> None:
    """全国の市町村役場等及び公的集会施設データ（ポイント）をダウンロードする。

    全国版 zip に入れ子で入っている 47 都道府県分の zip から GeoJSON を取り出し、
    features を連結した単一の FeatureCollection を出力する。都道府県の zip が
    欠けていれば KeyError で止める（欠けたまま統合すると行が減るだけでビルドは
    通ってしまうため）。一時ファイルに書き出してからリネームすることで、中断時に
    不完全な GeoJSON が統合済みとして残らないようにする。統合済みの場合は
    スキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    merged_path = dest / MERGED_GEOJSON
    if merged_path.exists():
        logger.info(f"  skip (already exists: {merged_path})")
        return

    logger.info("  downloading P05 public facility data...")
    req = Request(URL, headers={"User-Agent": "dataset-nlftp"})
    with urlopen(req) as resp:
        archive = io.BytesIO(resp.read())

    features: list[dict] = []
    crs = None
    with zipfile.ZipFile(archive) as outer:
        for pref in PREF_CODES:
            member = f"P05-22_{pref:02d}_GML.zip"
            with zipfile.ZipFile(io.BytesIO(outer.read(member))) as inner:
                name = f"P05-22_{pref:02d}.geojson"
                data = json.loads(inner.read(name).decode("utf-8"))
            crs = crs or data.get("crs")
            features.extend(data["features"])

    merged = {"type": "FeatureCollection", "crs": crs, "features": features}
    tmp_path = merged_path.with_suffix(".geojson.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False)
    tmp_path.rename(merged_path)

    logger.info(f"  public facility data ready in {dest} ({len(features)} features)")
